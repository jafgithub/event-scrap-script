import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import make_request
from datetime import datetime, timedelta, timezone
import json
from event import Event
from utils import get_lat_long
# Configure logging

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from pytz import timezone
import logging
import json

MEETUP_LOCATION_MAP = {
    "miami": "us--fl--Miami",
    "new jersey": "us--nj--Jersey+City",
    "islamabad": "pk--Islamabad",
    "bangalore": "in--Bangalore",
    "chennai": "in--Chennai",
    "dhaka": "bd--Dhaka",
}
def fetch_events_from_meetup(days=2, city="Miami"):
    try:
        results = []
        end_date = datetime.now() + timedelta(days=int(days))
        tz = timezone("America/New_York")  # adjust as needed

        # Build Meetup URL
        city_key = city.lower()

        location = MEETUP_LOCATION_MAP.get(city_key)
        if not location:
            raise ValueError(f"Unsupported city for Meetup: {city}")

        url = f"https://www.meetup.com/find/?location={location}&source=EVENTS"
        # url = f"https://www.meetup.com/find/?location=us--fl--{city_param}&source=EVENTS"

        events_data = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
            page = browser.new_page()

            def handle_response(response):
                if "gql2" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        if "data" in data:
                            events_data.append(data)
                    except:
                        pass

            page.on("response", handle_response)
            page.goto(url)

            # --- Scroll and wait loop for loading more events ---
            last_height = page.evaluate("() => document.body.scrollHeight")
            while True:
                page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000)  # wait 8s for new events to load
                new_height = page.evaluate("() => document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            page.wait_for_timeout(2000) 

        # --- Parse events ---
        for gql_response in events_data:
            try:
                if isinstance(gql_response, dict):
                    gql_response = [gql_response]

                if not isinstance(gql_response, list):
                    continue

                for item in gql_response:
                    data = item.get("data")
                    if not data:
                        continue

                    result = data.get("result")

                    # Only parse responses with "edges" (actual events)
                    if not isinstance(result, dict) or "edges" not in result:
                        continue

                    for edge in result["edges"]:
                        record = edge.get("node")
                        if not record:
                            continue

                        try:
                            # --- Venue / Group ---
                            venue = record.get("venue") or {}
                            group = record.get("group") or {}
                            place_name = venue.get("name") or group.get("name", "")
                            city_from_group = ""
                            if group.get("name") and "," in group["name"]:
                                city_from_group = group["name"].split(",")[-1].strip()

                            address = ", ".join(filter(None, [
                                venue.get("name"),
                                venue.get("city") or city_from_group,
                                venue.get("state")
                            ]))

                            # --- Image ---
                            featured_photo = record.get("featuredEventPhoto") or {}
                            image = featured_photo.get("highResUrl")

                            # --- Dates ---
                            try:
                                sdate_obj = datetime.fromisoformat(record["dateTime"])
                            except Exception:
                                logging.warning(f"Invalid start date format: {record.get('dateTime')}")
                                continue

                            edate_obj = None
                            if record.get("endTime"):
                                try:
                                    edate_obj = datetime.fromisoformat(record["endTime"])
                                except:
                                    pass

                            # --- Event Object ---
                            event = Event()
                            event["title"] = record.get("title", "")
                            event["description"] = record.get("description", "")
                            event["place_name"] = place_name
                            event["address"] = address
                            event["latitude"] = venue.get("lat")
                            event["longitude"] = venue.get("lon")
                            event["event category"] = "NONE"
                            event["event_url"] = record.get("eventUrl")
                            event["original_img_name"] = image if image else "NONE"
                            event["img"] = image if image else "NONE"
                            event["cover_img"] = event.get("img")

                            event["sdate"] = sdate_obj.strftime("%Y-%m-%d")
                            event["stime"] = sdate_obj.strftime("%H:%M:%S")
                            if edate_obj:
                                event["edate"] = edate_obj.strftime("%Y-%m-%d")
                                event["etime"] = edate_obj.strftime("%H:%M:%S")
                            else:
                                event["edate"] = None
                                event["etime"] = None

                            results.append(event)
                            logging.info(f"Event processed: {event['event_url']}")

                        except Exception:
                            logging.exception("Error while building single event object")

            except Exception:
                logging.exception("Error while parsing GraphQL response")

    except Exception:
        logging.exception("An error occurred in fetch_events_from_meetup")

    return results

# def fetch_events_from_meetup(days=2, city="Miami"):
#     try:
#         results = []
#         print(days)
#         lat, lng = get_lat_long(city)
#         print(lat, lng)
#         tz = timezone(timedelta(hours=-4))
#         start_time = datetime.now()
#         end_time = start_time + timedelta(days=int(days))
#         start_time = start_time.replace(tzinfo=tz)
#         end_time = end_time.replace(tzinfo=tz)
#         start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
#         end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
#         start_time = start_time[:-2] + ":" + start_time[-2:]
#         end_time = end_time[:-2] + ":" + end_time[-2:]

#         url = "https://www.meetup.com/gql2"

#         headers = {
#             'Content-Type': 'application/json',
#             'Cookie': 'MEETUP_INVALIDATE=-BtUS90z73Ehfk_v'
#         }
#         payload = {
#             "operationName": "recommendedEventsWithSeries",
#             "variables": {
#                 "first": 20,
#                 "lat": lat,
#                 "lon": lng,
#                 "topicCategoryId": None,
#                 "startDateRange": start_time,
#                 "endDateRange": end_time,
#                 "sortField": "DATETIME"
#             },
#             "extensions": {
#                 "persistedQuery": {
#                     "version": 1,
#                     "sha256Hash": "2461ce7745f8175aac6c500a5189fbc5a86e50b4603832f95036650c8b3fb697"
#                 }
#             }
#         }

#         logging.info(f"Start Time: {start_time}")
#         logging.info(f"End Time: {end_time}")
#         response = make_request(
#             url=url, request_type="POST", headers=headers, data=json.dumps(payload))
#         with open('res.json','w') as f:
#             json.dump(response, f, indent=4)
#         hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
#         cursor = response["data"]["result"]["pageInfo"]["endCursor"]
#         records = response["data"]["result"]["edges"]
#         payload["variables"]["after"] = cursor
#         records = [record["node"] for record in records]
#         while hasNextPage:
#             response = make_request(
#                 url=url, headers=headers, request_type="POST", data=json.dumps(payload))
#             hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
#             cursor = response["data"]["result"]["pageInfo"]["endCursor"]
#             payload["variables"]["after"] = cursor
#             _records = response["data"]["result"]["edges"]
#             tmp = [records.append(record["node"]) for record in _records]
#         else:
#             response = make_request(
#                 url=url, headers=headers, request_type="POST", data=json.dumps(payload))
#             hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
#             cursor = response["data"]["result"]["pageInfo"]["endCursor"]
#             payload["variables"]["after"] = cursor
#             _records = response["data"]["result"]["edges"]
#             tmp = [records.append(record["node"]) for record in _records]

#         print(len(records))
#         for i, record in enumerate(records):
#             try:
#                 address = f'{record["venue"]["name"] }, {record["venue"]["city"]}, {record["venue"]["state"]}'
#                 if address == ', , ':
#                     address = record["venue"]["name"]
#                 image = record["featuredEventPhoto"]["baseUrl"] if len(
#                     record["featuredEventPhoto"]) > 0 else "NONE"
#                 sdate = datetime.fromisoformat(record["dateTime"])
#                 edate = record.get("endTime",None) and datetime.fromisoformat(record.get("endTime",None))
#                 event = Event()
#                 event["title"] = record["title"]
#                 event["description"] = record["description"]
#                 if image == "NONE":
#                     event["img"], event["original_img_name"] = ("NONE", "NONE")
#                 else:
#                     # img_name, event["original_img_name"] = save_and_upload_image(
#                     #     image, "meetup.com")
#                     # event["img"] = f"images/event/{img_name}"
#                     event["original_img_name"] = image
#                 event["place_name"] = record["venue"]["name"]
#                 event["address"] = address
#                 event["latitude"] = record["venue"]["lat"]
#                 event["longitude"] = record["venue"]["lon"]
#                 event["event category"] = "NONE"
#                 event["cover_img"] = event["img"]
#                 event["sdate"] = sdate.strftime("%Y-%m-%d")
#                 event["stime"] = sdate.strftime("%H:%M:%S")
#                 event["etime"] = edate and edate.strftime("%H:%M:%S")
#                 event["edate"] = edate and edate.strftime("%Y-%m-%d")
#                 event["event_url"] = record["eventUrl"]
#                 results.append(event)
#                 logging.info(
#                     f"Event {i+1} processed successfully. {event['event_url']}"
#                 )
#                 print(event)
#             except Exception:
#                 logging.exception(
#                     "An error occurred while processing a record")
#     except Exception:
#         logging.exception("An error occurred")

#     return results

# Example usage:
# events = fetch_events_from_meetup()


if __name__ == "__main__":
    fetch_events_from_meetup()
