import logging, requests
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lxml.etree import _Element, _ElementTree
from lxml.html import HtmlElement

import config
from event import Event
from utils import (extract_values, make_request, read_json)
from requests_ip_rotator import ApiGateway,EXTRA_REGIONS,ALL_REGIONS


# def fetch_events_from_tentimes(days=1, *args, **kwargs):
#     _XPATHS = read_json(config.XPATH_DIR / '10times.json')
#     # print(_XPATHS)
#     page_count = 1

#     #preparing api getway for iprotation
#     gateway = ApiGateway(
#         site="https://10times.com/",
#         access_key_id=config.AWS_KEY_ID,
#         access_key_secret=config.AWS_SECRET_ACCESS_KEY,
#     )
#     d = gateway.start(force=True)
#     print(d)
#     results = []

#     while True:
        
#         headers = {
#             'Referer': 'https://10times.com/miami-us',
#             'Upgrade-Insecure-Requests': '1',
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
#             'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
#             'sec-ch-ua-mobile': '?0',
#             'sec-ch-ua-platform': '"Windows"',
#         }
#         session = requests.Session()
#         session.mount("https://10times.com/", gateway)

#         # params = {
#         #     "datefrom": "2023-09-28",
#         #     "dateto": "2023-10-12",
#         #     "ajax": "1",
#         #     "page": str(page_count),
#         #     "freelist": "1",
#         # }

#         response = make_request(
#             url="https://10times.com/miami-us", headers=headers, session=session
#         )
#         print(response)

#         # try block for each page
#         try:
#             if isinstance(response, (HtmlElement, _ElementTree, list)):
#                 events_list = response.xpath(_XPATHS["listpage"]["event_card"])
#                 # this events_list contains list of <tr> tags each one is an event
#                 # print("Event len :", len(events_list))
#                 # print(events_list)

#                 for event in events_list:
#                     event_url = extract_values(
#                         event.xpath(_XPATHS["listpage"]["event_url"])
#                     )

#                     # print(event_url)
#                     # try block for details page
#                     try:
#                         event_detail_page = make_request(event_url, session=session)

#                         if isinstance(
#                             event_detail_page, (_Element, HtmlElement, _ElementTree)
#                         ):
#                             # print("Hell")
#                             event_name = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["event_name"]
#                                 )
#                             )
#                             latitude = extract_values(
#                                 event_detail_page.xpath(_XPATHS["detailpage"]["lat"])
#                             )
#                             longitude = extract_values(
#                                 event_detail_page.xpath(_XPATHS["detailpage"]["long"])
#                             )
#                             image_url = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["event_image"]
#                                 )
#                             )
#                             desc = extract_values(
#                                 event_detail_page.xpath(_XPATHS["detailpage"]["desc"])
#                             )
#                             organizer = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["organizer"]
#                                 )
#                             )
#                             start_end_datetime = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["start_end_datetime"]
#                                 )
#                             )
#                             event_category = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["event_category"]
#                                 )
#                             )
#                             place_name = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["place_name"]
#                                 )
#                             )
#                             address = extract_values(
#                                 event_detail_page.xpath(
#                                     _XPATHS["detailpage"]["address"]
#                                 )
#                             )

#                             # dates and image_url needs specific parsing
#                             start_date = start_end_datetime.split(",")[0]
#                             start_date = datetime.fromtimestamp(int(start_date))

#                             end_date = start_end_datetime.split(",")[1]
#                             end_date = datetime.fromtimestamp(int(end_date))

#                             # image_url is in css backgroud-image property
#                             print(image_url)
#                             if image_url != "NONE":
#                                 image_url = image_url.split("(")[1].split(");")[0]
#                             else:
#                                 image_url = "NONE"
#                             # if image_url:
#                             #     image_url = save_and_upload_image(
#                             #         url=image_url, website_name="10times.com"
#                             #     )
#                             # if image_url == "NONE":
#                             #     file_name = "NONE"
#                             # else:
#                             #     file_name, image_url = image_url
#                             # if not image_url:
#                             #     image_url = "NONE"
#                             an_event = Event()

#                             an_event["title"] = event_name
#                             # an_event["img"] = f"images/event/{file_name}"
#                             # an_event["cover_img"] = f"images/event/{file_name}"
#                             an_event["sdate"] = start_date
#                             an_event["stime"] = "NONE"
#                             an_event["etime"] = "NONE"
#                             an_event["address"] = address
#                             an_event["description"] = desc
#                             an_event["disclaimer"] = "NONE"
#                             an_event["latitude"] = latitude
#                             an_event["longitude"] = longitude
#                             an_event["place_name"] = place_name
#                             an_event["event category"] = event_category
#                             an_event["organizer"] = organizer
#                             an_event["event_url"] = event_url
#                             an_event["edate"] = end_date
#                             an_event["original_img_name"] = image_url
#                             results.append(an_event)


#                             logging.info(f"Successfully fetched event: {event_url}.")

#                         else:
#                             logging.exception(
#                                 f"Failed to parse event detail page for URL: {event_url}."
#                             )
#                     except Exception:
#                         logging.exception(f"Error processing event: {event_url}")
#             else:
#                 logging.exception(
#                     f"Failed to fetch or parse the response from 10times.com : {page_count}"
#                 )
#                 break  # stopping because no events are there

#             page_count += 1

#             # break  # it's here for testing to just get one page
#         except Exception:
#             logging.exception(f"Invalid response for page {page_count}")

#     # returning results in the end
#     return results

def fetch_events_from_tentimes(days=1, *args, **kwargs):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from lxml import html
    from webdriver_manager.chrome import ChromeDriverManager

    _XPATHS = read_json(config.XPATH_DIR / '10times.json')
    results = []
    page_count = 1

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        while True:
            url = f"https://10times.com/miami-us?page={page_count}"
            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, _XPATHS["listpage"]["event_card"])
                    )
                )
            except:
                break  # no more pages

            page_source = driver.page_source
            response = html.fromstring(page_source)
            events_list = response.xpath(_XPATHS["listpage"]["event_card"])

            if not events_list:
                break

            for event in events_list:
                onclick_value = extract_values(
                    event.xpath(_XPATHS["listpage"]["event_url"])
                )

                if onclick_value and "window.open" in onclick_value:
                    event_url = onclick_value.split("window.open('")[1].split("'")[0]
                else:
                    event_url = "NONE"

                if not event_url:
                    continue

                driver.get(event_url)

                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//input[@id='event_name']")
                        )
                    )
                except:
                    continue

                detail_source = driver.page_source
                event_detail_page = html.fromstring(detail_source)

                event_name = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["event_name"]
                    )
                )

                latitude = extract_values(
                    event_detail_page.xpath(_XPATHS["detailpage"]["lat"])
                )

                longitude = extract_values(
                    event_detail_page.xpath(_XPATHS["detailpage"]["long"])
                )

                image_url = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["event_image"]
                    )
                )

                desc = extract_values(
                    event_detail_page.xpath(_XPATHS["detailpage"]["desc"])
                )

                organizer = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["organizer"]
                    )
                )

                start_end_datetime = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["start_end_datetime"]
                    )
                )

                event_category = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["event_category"]
                    )
                )

                place_name = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["place_name"]
                    )
                )

                address = extract_values(
                    event_detail_page.xpath(
                        _XPATHS["detailpage"]["address"]
                    )
                )

                # parse timestamps safely
                try:
                    start_ts, end_ts = start_end_datetime.split(",")
                    start_date = datetime.fromtimestamp(int(start_ts))
                    end_date = datetime.fromtimestamp(int(end_ts))
                except:
                    start_date = "NONE"
                    end_date = "NONE"

                if image_url != "NONE" and "url(" in image_url:
                    image_url = image_url.split("(")[1].split(")")[0]
                else:
                    image_url = "NONE"

                an_event = Event()
                an_event["title"] = event_name
                an_event["sdate"] = start_date
                an_event["edate"] = end_date
                an_event["stime"] = "NONE"
                an_event["etime"] = "NONE"
                an_event["address"] = address
                an_event["description"] = desc
                an_event["latitude"] = latitude
                an_event["longitude"] = longitude
                an_event["place_name"] = place_name
                an_event["event category"] = event_category
                an_event["organizer"] = organizer
                an_event["event_url"] = event_url
                an_event["original_img_name"] = image_url

                results.append(an_event)
                logging.info(f"Successfully fetched event: {event_url}")

            page_count += 1

    finally:
        driver.quit()

    return results

if __name__ == "__main__":
    fetch_events_from_tentimes()