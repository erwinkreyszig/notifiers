import logging
import os
from dataclasses import dataclass, field

from playwright.sync_api import Playwright, sync_playwright
from src.route_maps import BUS_NUMBER_URL_MAP


@dataclass
class BusLocator:
    route_urls: tuple[str]
    logger: logging.Logger
    _locations: dict = field(default_factory=dict)

    def run_playwright_context(self, headless: bool = True) -> None:
        for route_url in self.route_urls:
            with sync_playwright() as playwright:
                self.get_current_location(playwright, route_url, headless)

    def get_current_location(
        self, playwright: Playwright, route_url: str, headless: bool
    ) -> None:
        self.logger.info(f"Getting bus location from `{route_url}`.")
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        self.logger.info(f"Page opened{'(headless)' if headless else ''}.")
        if not headless:
            page.set_viewport_size({"width": 1600, "height": 900})
        page.goto(route_url)
        self.logger.info("Navigated to url.")
        title = page.title()
        route_key = self.__get_route_from_page_title(title)
        current_stop_locator = page.locator("div.congestion")
        if current_stop_locator.count() < 1:
            self.logger.info("Bus location indicator could not be found.")
            self._locations[route_key] = ["Not available."]
            return
        bus_area_divs = page.locator("div.busArea").filter(has=current_stop_locator)
        self.logger.info("Bus location indicator found. Looking up stop name(s).")
        bus_stop_names = []
        for bus_area_div in bus_area_divs.all():
            closest_point_area_div = bus_area_div.locator(
                "//preceding-sibling::*[contains(@class, 'pointArea')][1]"
            )
            bus_stop_name = closest_point_area_div.locator("a.busstopName").inner_text()
            self.logger.info(f"Stop name found: {bus_stop_name}")
            bus_stop_names.append(bus_stop_name)
        self._locations[route_key] = bus_stop_names

    def get_current_bus_locations(self):
        return self._locations

    def __get_route_from_page_title(self, page_title):
        self.logger.info("Getting page title.")
        to_remove = ("運行情報", "\xa0", " ", "|")
        empty_str = ""
        page_title_copy = page_title[:]
        for substr in to_remove:
            page_title_copy = page_title_copy.replace(substr, empty_str)
        self.logger.info(f"Cleaned page title: `{page_title_copy}`.")
        return page_title_copy


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL") or logging.INFO))
    route_number = "26"
    locator = BusLocator(BUS_NUMBER_URL_MAP[route_number], logging.getLogger(__name__))
    locator.run_playwright_context()
