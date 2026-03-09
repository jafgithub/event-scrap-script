import logging
from datetime import date, timedelta
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import pandas as pd
import time
from event import Event
# from utils import save_and_upload_image


def fetch_events_from_seatgeek(days=1, city="Miami",
                                max_retries=3,
                                max_pages=50):

    url = "https://api.seatgeek.com/2/events/"

    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        end_date_str = end_date.strftime("%Y-%m-%d")

        logging.info(
            f"Fetching events from seatgeek.com for {city} for next {days} days."
        )

        results = []
        session = requests.Session()

        params = {
            "page": 1,
            "per_page": 50,
            "listing_count.gte": 1,
            "lat": 25.76168,
            "lon": -80.191788,
            "range": "50mi",
            "datetime_utc.lte": end_date_str,
            "sort": "datetime_local.asc",
            "client_id": "MTY2MnwxMzgzMzIwMTU4",
        }

        page_number = 1

        while page_number <= max_pages:

            params["page"] = page_number
            success = False

            # ---- Retry per page ----
            for attempt in range(1, max_retries + 1):
                try:
                    logging.info(f"SeatGeek page {page_number}, attempt {attempt}")

                    response = session.get(
                        url,
                        params=params,
                        timeout=30
                    )

                    if response.status_code == 200:
                        success = True
                        break

                    elif response.status_code == 429:
                        logging.warning("Rate limited. Sleeping...")
                        time.sleep(5 * attempt)

                    else:
                        logging.warning(
                            f"Status {response.status_code} on page {page_number}"
                        )

                except requests.exceptions.RequestException:
                    logging.exception(
                        f"Network error page {page_number}, attempt {attempt}"
                    )

                time.sleep(2 * attempt)

            if not success:
                logging.error(f"Skipping page {page_number} after retries")
                page_number += 1
                continue

            try:
                data = response.json()
                events = data.get("events", [])
            except Exception:
                logging.exception("JSON parsing failed")
                break

            if not events:
                logging.info("No more events found")
                break

            logging.info(f"Fetched {len(events)} events from SeatGeek")

            # ---- Process events ----
            for i, record in enumerate(events):
                try:
                    an_event = Event()

                    an_event["title"] = record.get("title", "")
                    an_event["event_url"] = record.get("url", "")

                    venue_data = record.get("venue", {})
                    location_data = venue_data.get("location", {})

                    an_event["place_name"] = venue_data.get("name", "")
                    an_event["latitude"] = float(location_data.get("lat", 0))
                    an_event["longitude"] = float(location_data.get("lon", 0))

                    an_event["address"] = (
                        f"{venue_data.get('name','')}, "
                        f"{venue_data.get('address','')}, "
                        f"{venue_data.get('display_location','')} - "
                        f"{venue_data.get('postal_code','')}"
                    )

                    datetime_local = record.get("datetime_local", "")
                    if "T" in datetime_local:
                        sdate, stime = datetime_local.split("T")
                    else:
                        sdate, stime = None, None

                    an_event["sdate"] = sdate
                    an_event["stime"] = stime
                    an_event["etime"] = "NONE"
                    an_event["edate"] = "NONE"

                    an_event["description"] = (
                        record.get("description") or "NONE"
                    )

                    taxonomies = record.get("taxonomies", [])
                    an_event["event category"] = ", ".join(
                        [t.get("name", "") for t in taxonomies]
                    )

                    an_event["price"] = record.get(
                        "stats", {}
                    ).get("median_price", 0)

                    performers = record.get("performers", [])
                    if performers and performers[0].get("image"):
                        an_event["original_img_name"] = performers[0].get("image")
                    else:
                        an_event["original_img_name"] = "NONE"

                    results.append(an_event)

                except Exception:
                    logging.exception(
                        f"Error processing event {record.get('url')}"
                    )

            page_number += 1
            time.sleep(1)

        logging.info(f"SeatGeek finished. Total events: {len(results)}")
        return results

    except Exception:
        logging.exception("Fatal error in SeatGeek scraper")
        return []


if __name__ == "__main__":
    results = fetch_events_from_seatgeek()
    # if results:
    #     df = pd.DataFrame(results)

    #     file_name = f"seatgeek.xlsx"
    #     df.to_excel(file_name, index=False)

    #     logging.info(f"Excel file created successfully: {file_name}")

    # print(results)
