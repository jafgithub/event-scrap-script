import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from utils import make_request
from datetime import datetime, timedelta
from event import Event
from time import sleep

# Configure logging
logging.basicConfig(filename='events.log', level=logging.INFO)
import json
import traceback
def fetch_events_from_miamitimes(city="", days=2):
    try:
        start = datetime.now()
        end = start + timedelta(days=days)
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
        base_url = "https://discovery.evvnt.com/api/events"
        records = []
        result = []
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://www.miamitimesonline.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
        }

        for page in range(0, 10):  # first 5 pages only
            url = (
                f"{base_url}?multipleEventInstances=true"
                f"&publisher_id=8787"
                f"&hitsPerPage=30"
                f"&page={page}"
                f"&fromDate={start}"
                f"&toDate={end}"
            )
            res = make_request(url=url, headers=headers)
            if not res:
                continue

            records = res.get("events") or []
            logging.info(f"Fetched {len(records)} records")

            if not records:
                # No more pages / no events on this page
                break

            for i, record in enumerate(records):
                address = record.get("venue") or {}
                sdate = ""
                edate = ""
                event = Event()

                if record.get("start_time_i"):
                    sdate = datetime.fromtimestamp(int(record.get("start_time_i")))
                    event["sdate"] = sdate.strftime("%Y-%m-%d")
                    event["stime"] = sdate.strftime("%H:%M:%S")
                else:
                    event["sdate"] = "NONE"
                    event["stime"] = "NONE"

                if record.get("end_time_i"):
                    edate = datetime.fromtimestamp(int(record.get("end_time_i")))
                    event["edate"] = edate.strftime("%Y-%m-%d")
                    event["etime"] = edate.strftime("%H:%M:%S")
                else:
                    event["edate"] = "NONE"
                    event["etime"] = "NONE"

                if record.get("category_name", None):
                    event["event category"] = record["category_name"]
                logging.debug(record.get("category_name", None))

                _address = ""
                logging.info(f"Processing event {i+1}")
                if address:
                    _address = ""
                    if address.get("name"):
                        _address += f"{address['name']}"
                    if address.get("address_1"):
                        _address += f", {address['address_1']}"
                    if address.get("town"):
                        _address += f", {address['town']}"
                    if address.get("country"):
                        _address += f", {address['country']}"
                    if address.get("post_code"):
                        _address += f", {address['post_code']}"

                event["address"] = _address or "NONE"
                event["title"] = record.get("title") or "NONE"
                event["description"] = record.get("description") or "NONE"
                event["latitude"] = address.get("latitude") or "NONE"
                event["longitude"] = address.get("longitude") or "NONE"
                event["place_name"] = address.get("name") or "NONE"

                img_url = img_path = "NONE"
                images = None
                if record.get("images"):
                    if isinstance(record.get("images"), list):
                        images = record.get("images")[0] if record.get("images") else None
                    elif isinstance(record.get("images"), dict):
                        images = record.get("images")
                    if images:
                        img_url = images["original"]["url"]
                    else:
                        img_url = "NONE"

                event["original_img_name"] = img_url

                if record.get("source_broadcast_url"):
                    event["event_url"] = record.get("source_broadcast_url") or "NONE"
                    logging.info(f"Event {i+1} successfully fetched: {event['event_url']}")
                elif record.get("links", None):
                    links = record.get("links") or {}
                    logging.info(f"Processing links for event {i+1}: {links}")
                    if "Website" in links.keys():
                        event["event_url"] = links["Website"]
                        logging.info(f"Event {i+1} successfully fetched: {event['event_url']}")
                    elif "Tickets" in links.keys():
                        event["event_url"] = links.get("Tickets")
                        logging.info(f"Event {i+1} successfully fetched: {event['event_url']}")
                    elif "tickets" in links.keys():
                        event["event_url"] = links.get("tickets")
                        logging.info(f"Event {i+1} successfully fetched: {event['event_url']}")

                result.append(event)

        if result:
            return result
        else:
            logging.warning("No events found")

    except Exception:
        print(traceback.format_exc())
        logging.exception(f"An error occurred.")


if __name__ == "__main__":
    fetch_events_from_miamitimes(days=30)