import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import openmeteo_requests
import polars as pl
import requests_cache
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from retry_requests import retry
from slack_sdk import WebClient

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
KEY_HR_TEXT_MAP = {
    "precipitation_probability": "Rain %",
    "temperature_2m": "Temp",
    "apparent_temperature": "Temp °C",
    "relative_humidity_2m": "Rel. Humidity",
    "uv_index": "UV Index",
}


def get_geolocator(app_name):
    return Nominatim(user_agent=app_name)


def get_lat_long_from_address(address_string, geolocator, timeout=10):
    location = None
    error = None
    try:
        location = geolocator.geocode(address_string, timeout=timeout)
    except Exception as e:
        error = str(e)
    if location:
        lat_long = {
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        return lat_long, error
    return None, error


def get_weather_api_client():
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def get_start_and_end_dates_for_forecast(tz):
    today = datetime.now(tz)
    return {"start_date": today, "end_date": today + timedelta(days=1)}


def get_weather_variables():
    weather_variables = os.getenv("WEATHER_VARS")
    return list(map(str.strip, weather_variables.split(",")))


def generate_params_for_forecast_api(
    lat_long,
    date_range,
    timezone,
    weather_variables,
    temp_unit="celsius",
    date_format="%Y-%m-%d",
):
    date_range_strs = {
        key: value.strftime(date_format) for key, value in date_range.items()
    }
    return {
        **lat_long,
        "hourly": weather_variables,
        "timezone": timezone,
        **date_range_strs,
        "temperature_unit": temp_unit,
    }


def get_hourly_data_df(response, weather_variables):
    hourly = response.Hourly()
    hourly_data = {
        "timestamp": pl.datetime_range(
            start=datetime.fromtimestamp(hourly.Time()),
            end=datetime.fromtimestamp(hourly.TimeEnd()),
            interval="1h",
            closed="left",
            eager=True,
        ),
    }
    for index, var in enumerate(weather_variables):
        hourly_data[var] = hourly.Variables(index).ValuesAsNumpy()
    return pl.LazyFrame(hourly_data)


def should_include_tag(df):
    threshold = os.getenv("THRESHOLD_FOR_RAIN_TAG")
    if not threshold:
        return False
    return (
        not df.collect()
        .filter(pl.col("precipitation_probability") >= float(threshold))
        .is_empty()
    )


def generate_msg_content(df, current_day, weather_variables, include_tags=None):
    PIPE = " | "
    _df = df.collect()
    line_list = [["Time", *[KEY_HR_TEXT_MAP[var] for var in weather_variables]]]
    max_lens = list(map(len, line_list[0]))
    for row in _df.iter_rows():
        line = [row[0].strftime("%-H:%M")]
        for index, var in enumerate(weather_variables, 1):
            cell_value = int(row[index])
            if "probability" in var:
                cell_value = f"{cell_value}%"
            line.append(cell_value)
        line_list.append(list(map(str, line)))
        for index, val in enumerate(line):
            val_str_len = len(str(val))
            if val_str_len > max_lens[index]:
                max_lens[index] = val_str_len
    lines = [f"*Weather forecast for {current_day.strftime('%B %d, %Y')}*\n"]
    for i, ll in enumerate(line_list):
        _temp = []
        for cell_content, fill_length in zip(ll, max_lens):
            _temp.append(cell_content.ljust(fill_length))
        if i == 0:
            lines.append(f"```{PIPE.join(_temp)}\n")
        elif i == len(line_list) - 1:
            lines.append(f"{PIPE.join(_temp)}```")
        else:
            lines.append(f"{PIPE.join(_temp)}\n")
    if include_tags:
        lines.append(f"\n{include_tags}")
    return "".join(lines)


def get_slack_client(token):
    return WebClient(token=token)


def generate_mentions(user_id_list: list) -> str:
    return " ".join(f"<@{user_id}>" for user_id in user_id_list)


def send_slack_message(client, channel_id: str, message: str) -> None:
    return client.chat_postMessage(channel=channel_id, text=message)


def run_notifier():
    address_string = os.getenv("ADDRESS")
    if not address_string:
        logger.info("No set address, nothing else to do.")
        return
    logger.info(f"Set address is `{address_string}`.")
    geolocator = get_geolocator("my_notifier")
    lat_long, error = get_lat_long_from_address(address_string, geolocator)
    if lat_long is None:
        logger.info("Unable to get latitude and longitude, ending run.")
        return
    if error:
        logger.info(f"Encountered an error: `{error}`")
        return
    openmeteo = get_weather_api_client()
    tz_str = os.getenv("TIMEZONE") or "UTC"
    tz = ZoneInfo(tz_str)
    forecast_range = get_start_and_end_dates_for_forecast(tz)
    weather_variables = get_weather_variables()
    params = generate_params_for_forecast_api(
        lat_long,
        forecast_range,
        tz_str,
        weather_variables,
    )
    logger.info(f"Params for forecast api: {params}.")
    responses = openmeteo.weather_api(OPENMETEO_URL, params=params)
    if not responses or (responses and len(responses) < 1):
        logger.info("No response from weather api.")
        return
    logger.info("Weather forecast api data pulled.")
    current_day = forecast_range["start_date"]
    hourly_data_lf = get_hourly_data_df(responses[0], weather_variables)
    common_time_vars = {"minute": 0, "second": 0, "microsecond": 0, "tzinfo": None}
    naive_min_ts = current_day.replace(**{"hour": 8, **common_time_vars})
    naive_max_ts = current_day.replace(**{"hour": 21, **common_time_vars})
    hourly_data_lf = hourly_data_lf.filter(
        (pl.col("timestamp") >= naive_min_ts) & (pl.col("timestamp") <= naive_max_ts)
    )
    logger.info("Preparing slack notification.")
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_channel = os.getenv("SLACK_CHANNEL")
    slack_client = get_slack_client(slack_token)
    logger.info("Slack bot ready.")
    tags = None
    if should_include_tag(hourly_data_lf):
        logger.info("Including tags in slack message.")
        slack_mentions_str = os.getenv("SLACK_IDS")
        tags = generate_mentions(list(map(str.strip, slack_mentions_str.split(","))))
    slack_message = generate_msg_content(
        hourly_data_lf, current_day, weather_variables, include_tags=tags
    )
    response = send_slack_message(slack_client, slack_channel, slack_message)
    if type(response) is dict and not response["ok"]:
        logger.info(
            f"An error occurred during slack message sending: {response['error']}"
        )
    else:
        logger.info("Slack message sent.")


if __name__ == "__main__":
    logger = logging.getLogger()
    load_dotenv()
    run_notifier()
