import config
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging


class CustomWebDriver(webdriver.Chrome):
    def __init__(self, headless=True, is_eager=False, disable_images=False, is_none=False):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=en")

        if headless:
            options.add_argument("--headless=new")
        if is_none:
            options.page_load_strategy = "none"
        if is_eager:
            options.page_load_strategy = "eager"
        if disable_images:
            options.add_argument("--blink-settings=imagesEnabled=false")

        options.add_argument("--disable-extensions")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")

        service = Service(executable_path=str(config.DRIVER_PATH))

        super().__init__(service=service, options=options)
        self.maximize_window()

    def wait_for(self, expected_condition, *ec_args, timeout=10):
        try:
            condition_function = getattr(EC, expected_condition, None)
            if condition_function:
                try:
                    element = WebDriverWait(self, timeout).until(
                        condition_function(*ec_args)
                    )
                except Exception:
                    element = WebDriverWait(self, timeout).until(
                        condition_function(ec_args)
                    )
                return element
        except Exception:
            logging.exception("Element not found:")
            return None
