import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import make_request
from datetime import datetime, timedelta, timezone
import json
from event import Event

# Configure logging


def get_lat_long(city):
    url = "https://www.meetup.com/gql"

    headers = {
        'Content-Type': 'text/plain',
        'Cookie': 'MEETUP_INVALIDATE=iWGUcxc0WlG9coUK; MEETUP_INVALIDATE=dNVdWk3scz2H3n0g'
    }
    payload = json.dumps({
        "operationName": "locationWithInput",
        "variables": {
            "query": city
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "55a21eb6c958816ff0ae82a3253156d60595177b4f3c20b59ea696e97acc653d"
            }
        }
    })
    res = make_request(url=url, data=payload,
                       headers=headers, request_type="POST")
    lat = 0
    lng = 0
    if "searchedLocations" in res["data"]:
        lat = res["data"]["searchedLocations"][0]["lat"]
        lng = res["data"]["searchedLocations"][0]["lon"]
        return lat, lng


def fetch_events_from_meetup(days=2, city="Miami"):
    try:
        results = []
        print(days)
        lat, lng = get_lat_long(city)
        print(lat, lng)
        tz = timezone(timedelta(hours=-4))
        start_time = datetime.now()
        end_time = start_time + timedelta(days=int(days))
        start_time = start_time.replace(tzinfo=tz)
        end_time = end_time.replace(tzinfo=tz)
        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        start_time = start_time[:-2] + ":" + start_time[-2:]
        end_time = end_time[:-2] + ":" + end_time[-2:]

        url = "https://www.meetup.com/gql2"

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'MEETUP_INVALIDATE=-BtUS90z73Ehfk_v'
        }
        payload = {
            "operationName": "recommendedEventsWithSeries",
            "variables": {
                "first": 20,
                "lat": lat,
                "lon": lng,
                "topicCategoryId": None,
                "startDateRange": start_time,
                "endDateRange": end_time,
                "sortField": "DATETIME"
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "2461ce7745f8175aac6c500a5189fbc5a86e50b4603832f95036650c8b3fb697"
                }
            }
        }

        logging.info(f"Start Time: {start_time}")
        logging.info(f"End Time: {end_time}")
        response = make_request(
            url=url, request_type="POST", headers=headers, data=json.dumps(payload))
        # print(response)
        hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
        cursor = response["data"]["result"]["pageInfo"]["endCursor"]
        records = response["data"]["result"]["edges"]
        payload["variables"]["after"] = cursor
        records = [record["node"] for record in records]
        while hasNextPage:
            response = make_request(
                url=url, headers=headers, request_type="POST", data=json.dumps(payload))
            hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
            cursor = response["data"]["result"]["pageInfo"]["endCursor"]
            payload["variables"]["after"] = cursor
            _records = response["data"]["result"]["edges"]
            tmp = [records.append(record["node"]) for record in _records]
        else:
            response = make_request(
                url=url, headers=headers, request_type="POST", data=json.dumps(payload))
            hasNextPage = response["data"]["result"]["pageInfo"]["hasNextPage"]
            cursor = response["data"]["result"]["pageInfo"]["endCursor"]
            payload["variables"]["after"] = cursor
            _records = response["data"]["result"]["edges"]
            tmp = [records.append(record["node"]) for record in _records]

        print(len(records))
        for i, record in enumerate(records):
            try:
                address = f'{record["venue"]["name"] }, {record["venue"]["city"]}, {record["venue"]["state"]}'
                if address == ', , ':
                    address = record["venue"]["name"]
                image = record["featuredEventPhoto"]["baseUrl"] if len(
                    record["featuredEventPhoto"]) > 0 else "NONE"
                sdate = datetime.fromisoformat(record["dateTime"])
                edate = record.get("endTime",None) and datetime.fromisoformat(record.get("endTime",None))
                event = Event()
                event["title"] = record["title"]
                event["description"] = record["description"]
                if image == "NONE":
                    event["img"], event["original_img_name"] = ("NONE", "NONE")
                else:
                    # img_name, event["original_img_name"] = save_and_upload_image(
                    #     image, "meetup.com")
                    # event["img"] = f"images/event/{img_name}"
                    event["original_img_name"] = image
                event["place_name"] = record["venue"]["name"]
                event["address"] = address
                event["latitude"] = record["venue"]["lat"]
                event["longitude"] = record["venue"]["lon"]
                event["event category"] = "NONE"
                event["cover_img"] = event["img"]
                event["sdate"] = sdate.strftime("%Y-%m-%d")
                event["stime"] = sdate.strftime("%H:%M:%S")
                event["etime"] = edate and edate.strftime("%H:%M:%S")
                event["edate"] = edate and edate.strftime("%Y-%m-%d")
                event["event_url"] = record["eventUrl"]
                results.append(event)
                logging.info(
                    f"Event {i+1} processed successfully. {event['event_url']}"
                )
                print(event)
            except Exception:
                logging.exception(
                    "An error occurred while processing a record")
    except Exception:
        logging.exception("An error occurred")

    return results

# Example usage:
# events = fetch_events_from_meetup()


if __name__ == "__main__":
    fetch_events_from_meetup()
