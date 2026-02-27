import json
import time
import logging
import re
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from selenium.webdriver.common.by import By

from event import Event
from driver import CustomWebDriver

cookies_dict = {}

def get_api_params(driver: CustomWebDriver, city: str = "miami", days: int = 30):
    """
    Eventbrite has changed UI many times.
    Instead of clicking UI elements, we:
      - load city event page directly
      - read csrf token from cookies
      - read placeId from embedded scripts
    """

    try:
        url = f"https://www.eventbrite.com/d/{city.lower().replace(' ', '-')}/all-events/"
        driver.get(url)
        time.sleep(4)

        # ------------------ CSRF TOKEN ------------------
        csrf_token = None

        try:
            for cookie in driver.get_cookies():
                cookies_dict[cookie["name"]] = cookie["value"]
                if "csrf" in cookie["name"].lower():
                    csrf_token = cookie["value"]
                    break
        except Exception:
            csrf_token = None

        # ------------------ PLACE ID ------------------
        place_id = None
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for s in scripts:
                txt = (s.get_attribute("innerHTML") or "")
                m = re.search(r'"placeId":"(.*?)"', txt)
                if m:
                    place_id = m.group(1)
                    break
        except Exception:
            place_id = None

        if not csrf_token or not place_id:
            logging.error("Could not extract Eventbrite API parameters.")
            return None

        return place_id, csrf_token

    except Exception:
        logging.exception("Error occurred while retrieving API Params.")
        return None


def scrape_event_data(place_id, csrf_token, dates):

    try:
        url = "https://www.eventbrite.com/api/v3/destination/search/"

        headers = {
            "content-type": "application/json",
            "origin": "https://www.eventbrite.com",
            "referer": "https://www.eventbrite.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            'X-Requested-With': 'XMLHttpRequest',
            "X-CSRFToken": csrf_token,
            "x-csrftoken": csrf_token,
            "X-CSRF-Token": csrf_token,
        }

        data = {
            "event_search": {
                "dates": "current_future",
                "date_range": {"from": dates["start_date"], "to": dates["end_date"]},
                "dedup": True,
                "places": [place_id],
                "page": 1,
                "page_size": 50,
            },
            "expand.destination_event": [
                "primary_venue",
                "image",
                "ticket_availability",
                "primary_organizer",
            ],
        }

        results = []
        page_number = 1

        while True:
            data["event_search"]["page"] = page_number

            response = requests.post(url, headers=headers, cookies=cookies_dict, json=data)
            response_json = response.json()

            event_results = response_json.get("events", {}).get("results", [])

            if not event_results:
                break

            for event in event_results:
                try:
                    an_event = Event()

                    an_event["title"] = event["name"]
                    an_event["description"] = event.get("summary", "")

                    an_event["sdate"] = event["start_date"]
                    an_event["edate"] = event["end_date"]

                    an_event["stime"] = event["start_time"]
                    an_event["etime"] = event["end_time"]

                    venue = event.get("primary_venue", {})
                    addr = venue.get("address", {})

                    an_event["place_name"] = venue.get("name", "")
                    an_event["address"] = addr.get("localized_address_display", "")

                    an_event["latitude"] = float(addr.get("latitude", 0) or 0)
                    an_event["longitude"] = float(addr.get("longitude", 0) or 0)

                    an_event["organizer"] = event.get(
                        "primary_organizer", {}
                    ).get("name", "")

                    an_event["event_url"] = event.get("url", "")

                    image = event.get("image", None)
                    if image:
                        an_event["original_img_name"] = image["original"]["url"]
                    else:
                        an_event["original_img_name"] = "NONE"

                    results.append(an_event)

                except Exception:
                    logging.exception("Error while processing event")
                    continue

            page_number += 1

        return results

    except Exception:
        logging.exception("Error occurred while scraping event data")
        return []


def fetch_events_from_eventbrite(city="miami", days=7):
    try:
        driver = CustomWebDriver(headless=True)
        params = get_api_params(driver, city, days)
        driver.quit()

        if not params:
            logging.error("Could not get Eventbrite API params — exiting")
            return []

        place_id, csrf_token = params

        dates = {
            "start_date": datetime.today().strftime("%Y-%m-%d"),
            "end_date": (datetime.today() + timedelta(days)).strftime("%Y-%m-%d"),
        }

        return scrape_event_data(place_id, csrf_token, dates)

    except Exception:
        logging.exception("Error occurred during event data scraping and processing")
        return []


if __name__ == "__main__":
    print(fetch_events_from_eventbrite())

