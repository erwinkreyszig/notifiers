import asyncio  # noqa
import logging
import time
from dataclasses import dataclass, field

from playwright.async_api import Playwright, async_playwright


@dataclass
class BusLocator:
    route_urls: tuple[str]
    logger: logging.Logger
    _locations: dict = field(default_factory=dict)

    async def run_playwright_context(self, headless: bool = True) -> None:
        for route_url in self.route_urls:
            async with async_playwright() as playwright:
                await self.get_current_location(playwright, route_url, headless)

    async def get_current_location(
        self, playwright: Playwright, route_url: str, headless: bool
    ) -> None:
        start = time.perf_counter()
        self.logger.info(f"Getting bus location from `{route_url}`.")
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        self.logger.info(f"Page opened{'(headless)' if headless else ''}.")
        if not headless:
            page.set_viewport_size({"width": 1600, "height": 900})
        await page.goto(route_url)
        self.logger.info("Navigated to url.")
        current_stop_locator = page.locator("div.congestion")
        current_stop_locator_count = await current_stop_locator.count()
        if current_stop_locator_count < 1:
            self.logger.info("Bus location indication could not be found.")
            duration = time.perf_counter() - start
            self.logger.info(f"Operation took {duration:.2f} seconds.")
            return
        title = await page.title()
        destination = self.__get_destination_from_page_title(title)
        bus_area_divs = page.locator("div.busArea").filter(has=current_stop_locator)
        self.logger.info("Bus location indicator found. Looking up stop name(s).")
        all_bus_area_divs = await bus_area_divs.all()
        for bus_area_div in all_bus_area_divs:
            closest_point_area_div = bus_area_div.locator(
                "//preceding-sibling::*[contains(@class, 'pointArea')][1]"
            )
            bus_stop_name = await closest_point_area_div.locator(
                "a.busstopName"
            ).inner_text()
            self.logger.info(f"Stop name found: {bus_stop_name}")
            self._locations.setdefault(destination, []).append(bus_stop_name)
        await browser.close()
        duration = time.perf_counter() - start
        self.logger.info(f"Operation took {duration:.2f} seconds.")

    def get_current_bus_locations(self) -> dict:
        return self._locations

    def __get_destination_from_page_title(self, page_title: str) -> str:
        self.logger.info("Getting destination.")
        try:
            index_of_hatsu = page_title.index("発") + 1
        except (ValueError, TypeError):
            index_of_hatsu = 0
        cleaned_destination = page_title[index_of_hatsu:]
        empty_str = ""
        replace_items = {
            "\xa0": empty_str,
            " ": empty_str,
            "|": empty_str,
            ")": empty_str,
            "(": empty_str,
            "ゆき": empty_str,
        }
        for substr, replacement in replace_items.items():
            cleaned_destination = cleaned_destination.replace(substr, replacement)
        self.logger.info(f"Got destination: `{cleaned_destination}`")
        return cleaned_destination


if __name__ == "__main__":
    pass
