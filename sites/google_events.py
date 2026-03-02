import logging
import re
import time
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parsel import Selector
from selenium.common.exceptions import WebDriverException

from driver import CustomWebDriver
from event import Event
from utils import preprocess_date_string, get_driver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

def extract_text_from_html(html,cls):
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div", class_=cls)
    return element.get_text(strip=True) if element else None


def scroll_page(driver: CustomWebDriver, url):
    try:
        driver.get(url)
        # print(url)
        # print(driver.title)
        # print(driver.page_source)
        # user_agent = driver.execute_script('return navigator.userAgent;')
        # driver
        # print(user_agent)
        old_height = driver.execute_script(
            """
            function getHeight() {
                let a = document.querySelector('.UbEfxe').scrollHeight;
                return a
            }
            return getHeight();
        """
        )

        # print("sd", driver.execute_script(
        #     """
        #     return document.title;
        # """
        # ))

        while True:
            driver.execute_script(
                "document.querySelector('.UbEfxe').scrollTo(0, document.querySelector('.UbEfxe').scrollHeight);"
            )
            time.sleep(4)

            new_height = driver.execute_script(
                """
                function getHeight() {
                    return document.querySelector('.UbEfxe').scrollHeight;
                }
                return getHeight();
            """
            )

            if new_height == old_height:
                break

            old_height = new_height
        time.sleep(10)
        selector = Selector(driver.page_source)
        # driver.quit()

        return selector
    except WebDriverException as e:
        # Log the error
        logging.exception(f"Error occurred while scrolling the page: {e}")
        # Raise the error to propagate it further
        raise

    except Exception:
        # Log other unexpected exceptions
        logging.exception("An unexpected error occurred while scrolling the page")
        # Raise the error to propagate it further
        raise


def scrape_google_events(driver: CustomWebDriver, events_until_date, selector: Selector):
    try:
        results = []  # storing events
        ev=driver.find_elements(By.CLASS_NAME, "odIJnf")
        logging.info(f"Events found: {len(selector.css('.odIJnf'))}")
        count=-1
        for event in selector.css(".odIJnf")[:]:
            try:
                
                count+=1
                an_event = Event()
                # eid = create_unique_object_id()
                event_title = event.css(".YOGjf").get()
                event_title = extract_text_from_html(event_title, "YOGjf")
                date1= event.css('.UIaQzd').get()
                date1=extract_text_from_html(date1, "UIaQzd")
                date2=event.css('.wsnHcb').get()
                date2=extract_text_from_html(date2, "wsnHcb")
                date_start = f"{date1} {date2}"
                date_start = preprocess_date_string(date_string=date_start)

                if date_start > events_until_date:
                    continue

                date_when = event.css(".cEZxRc").get()
                date_when=extract_text_from_html(date_when, "cEZxRc")
                full_add = [
                    part.get() for part in event.css(".zvDXNd")
                ]
                full_address=[]
                for f in full_add:
                    add=extract_text_from_html(f, "zvDXNd")
                    full_address.append(add)
                full_address = filter(None, full_address)
                full_address = ", ".join(full_address)
                try:
                    full_address=full_address.replace("('","")
                    full_address=full_address.replace("',)","")
                except:
                    pass
                event_url=""
                location_link=""
                #driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ev[count])
                #time.sleep(2)
                #driver.execute_script("arguments[0].click();", ev[count])
                #wait = WebDriverWait(driver, 15)
#
                #event_container = wait.until(
                #    EC.presence_of_element_located((By.CSS_SELECTOR, '[jsname="qlMead"]'))
                #)
                eve=ev[count].find_elements(By.TAG_NAME, "a")
                if eve:
                    for a in eve:
                        if "/maps/" in a.get_attribute("href"):
                            location_link=a.get_attribute("href")
                            break
                    for a in eve:
                        if not "/maps/" in a.get_attribute("href"):
                            event_url=a.get_attribute("href")
                            break
                
                image_url = file_name = "NONE"
                image_url = event.css(".YQ4gaf.wA1Bge::attr(src)").get("")
                if not image_url:
                    # pass
                    # image_url = save_and_upload_image(
                    #     image_url, website_name="googleevents"
                    # )t
                    # if image_url == "NONE":
                        file_name = "NONE"
                    # else:
                    #     file_name, image_url = image_url

                # else:
                    # image_url = "NONE"
                description = event.css(".PVlUWc").get("")
                if description:
                    description=extract_text_from_html(description, "PVlUWc")
                place_name = event.css(".RVclrc").get()
                if place_name:
                    place_name=extract_text_from_html(place_name, "RVclrc")
                #venue_link = (
                #    "https://www.google.com" + event.css(".pzNwRe a::attr(href)").get()
                #    if event.css(".pzNwRe a::attr(href)").get()
                #    else None
                #)

                an_event["title"] = event_title
                # an_event["img"] = f"images/event/{file_name}"
                # an_event["cover_img"] = f"images/event/{file_name}"
                an_event["sdate"] = date_start
                an_event["stime"] = "NONE"
                an_event["etime"] = "NONE"
                an_event["address"] = (full_address,)
                an_event["description"] = description
                an_event["disclaimer"] = "NONE"
                an_event["place_name"] = place_name
                an_event["event category"] = "NONE"
                an_event["address_url"] = location_link
                an_event["event_url"] = event_url
                an_event["edate"] = date_when
                an_event["original_img_name"] = image_url

                results.append(an_event)  # appending the newly created event
                logging.info(
                    f"Event {an_event['id']} processed successfully. {an_event['event_url']}"
                )
            except KeyError:
                logging.exception(
                    f"KeyError: occurred while processing Event {an_event['id']}. url = {an_event['event_url']}"
                )

        return results
    except Exception:
        logging.exception("An unexpected error occurred while scraping Google events")
        # Raise the error to propagate it further
        raise


# def scrap_geo_code(driver: CustomWebDriver, events: list):
#     try:
#         for i, event in enumerate(events):
#             try:
#                 location_link = event["address_url"]
#                 driver.get(location_link)

#                 check_new_url = driver.wait_for(
#                     "url_changes", location_link, timeout=30
#                 )

#                 if check_new_url:
#                     new_url = driver.current_url

#                     pattern = r"@([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)"
#                     match = re.search(pattern, new_url)

#                     if match:
#                         latitude = match.group(1)
#                         longitude = match.group(2)
#                         events[i]["latitude"] = latitude
#                         events[i]["longitude"] = longitude
                        
#                         print("good")
#                         # print("Latitude:", latitude)
#                         # print("Longitude:", longitude)
#                     else:
#                         print("Latitude and longitude not found in the URL.")
#                 else:
#                     pass
#             except Exception:
#                 logging.exception(
#                     "An unexpected error occurred while scraping geocode data"
#                 )
#                 event["latitude"] = "NONE"
#                 event["longitude"] = "NONE"
#                 continue

#         driver.quit()
#         return events
#     except Exception:
#         logging.exception("An unexpected error occurred while scraping geocode data")
from urllib.parse import quote
def scrap_geo_code(driver, events: list):
    """
    Scrape latitude and longitude from Google Maps URLs for a list of events.

    Args:
        driver: Selenium WebDriver instance.
        events: List of dicts, each with 'address_url'.

    Returns:
        Updated list of events with 'latitude' and 'longitude'.
    """
    for i, event in enumerate(events):
        location_link = event.get("address_url")
        
        if not location_link:
            logging.warning(f"Event {i} has empty or missing address_url.")
            event["latitude"] = "NONE"
            event["longitude"] = "NONE"
            continue
        
        # Ensure proper URL format
        if not location_link.startswith(("http://", "https://")):
            location_link = "https://" + location_link

        # URL-encode any unsafe characters
        location_link = quote(location_link, safe=":/?&=#")
        
        try:
            driver.get(location_link)

            # Wait for URL to change (if you have a custom wait)
            check_new_url = driver.wait_for("url_changes", location_link, timeout=30)

            if not check_new_url:
                logging.warning(f"URL did not change for event {i}: {location_link}")
                event["latitude"] = "NONE"
                event["longitude"] = "NONE"
                continue

            new_url = driver.current_url
            pattern = r"@([-+]?[0-9]*\.?[0-9]+),([-+]?[0-9]*\.?[0-9]+)"
            match = re.search(pattern, new_url)

            if match:
                event["latitude"] = match.group(1)
                event["longitude"] = match.group(2)
                print(f"Event {i} - Latitude: {event['latitude']}, Longitude: {event['longitude']}")
            else:
                logging.warning(f"Lat/Lng not found in URL for event {i}: {new_url}")
                event["latitude"] = "NONE"
                event["longitude"] = "NONE"

        except Exception:
            logging.exception(f"Unexpected error scraping geocode data for event {i}")
            event["latitude"] = "NONE"
            event["longitude"] = "NONE"

    return events

        # Raise the error to propagate it further
        # raise e


def fetch_events_from_google_events(city="San Fransisco", days=30):
    try:
        logging.info(f"Google events scraping started for {city}")

        params = {
            "q": f"Events in {city}",  # search query
            "ibp": "htl;events",  # Google Events page
            "hl": "en",  # language
            "gl": "us",  # country of the search
        }

        events_until_date = datetime.now() + timedelta(days=days)
        # print(events_until_date)
        URL = f"https://www.google.com/search?q={params['q']}&ibp={params['ibp']}&hl={params['hl']}&gl={params['gl']}l"

        driver = CustomWebDriver()
        # driver = get_driver()
        result = scroll_page(driver, URL)
        google_events = scrape_google_events(
            driver, events_until_date=events_until_date, selector=result
        )
        print(len(google_events))
        # with open('raw.txt', 'w') as f:
        #     f.write(str(google_events))
        google_events_w_cords = scrap_geo_code(driver, google_events)

        logging.info(
            f"Google events scrapped successfully. Events scraped: {len(google_events_w_cords)}"
        )
        # Raise the error to propagate it further
        # if google_events_w_cords:
        #     df = pd.DataFrame(google_events_w_cords)

        #     file_name = f"google_events_{city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        #     df.to_excel(file_name, index=False)
        #     logging.info(f"Excel file created successfully: {file_name}")
        return google_events_w_cords
    except Exception:
        logging.exception("An unexpected error occurred in the main() function")
        # Raise the error to propagate it further
        raise


if __name__ == "__main__":
    fetch_events_from_google_events()