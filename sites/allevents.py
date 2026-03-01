import json
import logging
import time
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import aiohttp
import asyncio

import requests
from bs4 import BeautifulSoup

from event import Event
from utils import create_unique_object_id,GoogleDriveUploader

logging.basicConfig(
    filename="event_fetch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

url = "https://allevents.in/api/index.php/categorization/web/v1/list"
headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Cookie": "a=a;",
    "Referer": "https://allevents.in/hollywood/all?ref=cityhome-popmenuf",
}


def fetch_events_from_allevents(days=1, city="Miami"):
    url = "https://allevents.in/api/index.php/categorization/web/v1/list"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": "a=a;",
        "Referer": "https://allevents.in/hollywood/all?ref=cityhome-popmenuf",
    }

    try:
        event_urls = []
        events = []
        results = []

        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)

        logging.info(
            f"Fetching events from allevents.in for {city} for the next {days} days."
        )
        # Pagination loop
        page = 1
        max_pages = 10  # Safety limit
        # max_pages = 50  # Safety limit
        total_events_fetched = 0

        while page <= max_pages:
            data = {
                "venue": 0,
                "page": page,
                "rows": 1000,  # Use 100 (max per page)
                "tag_type": None,
                "sdate": start_date.timestamp(),
                "edate": end_date.timestamp(),
                "city": city,
                "keywords": 0,
                "category": ["all"],
                "formats": 0,
                "popular": True,
            }

            logging.info(f"Fetching page {page} from allevents.in...")
            
            response = requests.post(url, data=json.dumps(data), headers=headers, timeout=30)
            
            if response.status_code != 200:
                logging.error(f"Request failed with status code {response.status_code} on page {page}")
                break

            response_data = response.json()
            try:
                events_data = response_data.get("item", [])
            except:
                logging.info(f"No more events found. Stopped at page {page}")
                break
            if not events_data:
                logging.info(f"No more events found. Stopped at page {page}")
                break

            total_events_fetched += len(events_data)
            logging.info(f"Page {page}: Fetched {len(events_data)} events (Total: {total_events_fetched})")

            # Collect event URLs for this page
            page_event_urls = [record["event_url"] for record in events_data]
            event_urls.extend(page_event_urls)

            # Get descriptions for this page
            descriptions = get_desc(page_event_urls)

            # Process events from this page
            for i, record in enumerate(events_data):
                try:
                    stime = datetime.fromtimestamp(int(record["start_time"]))
                    etime = datetime.fromtimestamp(int(record["end_time"]))

                    eid = create_unique_object_id()
                    event_name = record["eventname_raw"]
                    event_url = record["event_url"]
                    venue = record["location"]
                    image_url = record.get("banner_url", "NONE")
                    
                    if not image_url:
                        image_url = "NONE"

                    start_time = stime.time()
                    end_time = etime.time()
                    start_date_obj = stime.date()
                    end_date_obj = etime.date()
                    latitude = float(record["venue"]["latitude"])
                    longitude = float(record["venue"]["longitude"])
                    full_address = record["venue"]["full_address"]
                    description = descriptions[i]
                    categories = record.get("categories") and record.get("categories")[0] or "No Categories Provided"
                    ticket_price = record["tickets"].get("min_ticket_price", 0)
                    an_event = Event()
                    an_event["title"] = event_name
                    an_event["sdate"] = start_date_obj
                    an_event["stime"] = start_time
                    an_event["etime"] = end_time
                    an_event["address"] = full_address
                    an_event["description"] = description
                    an_event["disclaimer"] = "NONE"
                    an_event["latitude"] = latitude
                    an_event["longitude"] = longitude
                    an_event["place_name"] = venue
                    an_event["event category"] = categories
                    an_event["price"] = ticket_price
                    an_event["event_url"] = event_url
                    an_event["edate"] = end_date_obj
                    an_event["original_img_name"] = image_url
                    
                    results.append(an_event)
                    #logging.info(f"Event processed: {event_url}")
                    
                except KeyError as e:
                    logging.exception(
                        f"KeyError occurred while processing event. url = {record.get('event_url', 'unknown')}, error: {e}"
                    )
                except Exception as e:
                    logging.exception(
                        f"Error processing event. url = {record.get('event_url', 'unknown')}, error: {e}"
                    )

        
            page += 1
            time.sleep(0.5)  # Be nice to the API

        logging.info(f"Successfully fetched {len(results)} events from allevents.in")
        return results
    except Exception:
        logging.exception(f"An error occurred while fetching events from allevents.in")
import pandas as pd
def get_desc(urls=None):
    if urls is None:
        logging.exception("URLs are not provided")
        raise ValueError("URLs are not provided")
    descriptions = []
    logging.info("Fetching event descriptions from allevents.in")
    for i, url in enumerate(urls):
        try:
            response = requests.get(url)
            html_content = response.content
            soup = BeautifulSoup(html_content, "html.parser")
            element = soup.find("div", class_="event-description-html")
            data = element.get_text(strip=True) if element is not None else ""
            descriptions.append(data)
        except Exception:
            logging.warning(
                f"An error occurred while fetching event description for URL {url}."
            )
            descriptions.append("")
    logging.info("Fetched event descriptions from allevents.in")

    return descriptions


if __name__ == "__main__":
    events = fetch_events_from_allevents(days=30)
    # if events:
    #     df = pd.DataFrame(events)

    #     file_name = f"allevents_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    #     df.to_excel(file_name, index=False)

    #     logging.info(f"Excel file created successfully: {file_name}")
    #     print(f"Excel created: {file_name}")
    async def main():
        uploader = GoogleDriveUploader()

        async with aiohttp.ClientSession(trust_env=True) as session:
            tasks = []

            for event in events:
                url = event["original_img_name"]
                if url.lower() != "none":
                    task = asyncio.create_task(uploader.download_and_upload_image(url=url,session=session))
                    tasks.append(task)
                else:
                    tasks.append("NONE")
            results = await asyncio.gather(*tasks)
            print(results)
            for result in results:
                print(result)
    
    asyncio.run(main())
