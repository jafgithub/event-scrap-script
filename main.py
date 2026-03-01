# import os
# import datetime
# import logging
# import sys

# import asyncio
# import aiohttp
# from aiohttp import ClientTimeout

# from utils import GoogleDriveUploader, GoogleDriveUploaderAsync

# from datetime import datetime

# from args_parser import WEBSITE_FUNCTIONS, parse_arguments
# # from utils import generate_xslx


# def fetch_events(website, city, days):
#     try:
#         events_fetch_function = WEBSITE_FUNCTIONS.get(website)
#         if events_fetch_function is None:
#             raise ValueError("Invalid website name.")

#         events = events_fetch_function(city=city.capitalize(), days=days)
#         return events
#     except Exception:
#         logging.exception(f"An error occurred while fetching events.")


# async def main():
#     try:
#         parser, args = parse_arguments()

#         if len(sys.argv) == 1:
#             parser.print_help()
#             print("No arguments provided. Use -h or --help for usage information.")
#             sys.exit(1)

#         website = args.website
#         city = args.city
#         days = args.days
        
#         # setup_logging()         ##### calling up logging function to intilize logging globally
        
#         events = fetch_events(website, city, days)
#         logging.info(f"Number of events found: {len(events)}")

#         # uploader = GoogleDriveUploader()
#         async with GoogleDriveUploaderAsync() as uploader:
#             timeout = ClientTimeout(total=14400)
#             async with aiohttp.ClientSession(trust_env=True,timeout=timeout) as session:
#                 tasks = []

#                 for event in events:
#                     url = event["original_img_name"]

#                     # print("URL in main", repr(url))
#                     # if url.lower() != "none":
#                     task = asyncio.create_task(uploader.download_and_upload_image(url=url, session=session))
#                     tasks.append(task)
                
#                 results = await asyncio.gather(*tasks)
#                 # print(results)

#                 for event,result in zip(events,results):
#                     if isinstance(result,tuple):
                        
#                         img_path,img_url = result
#                         event["img"] = event["cover_img"] = img_path
#                         event["original_img_name"] = img_url
#                     else:
#                         event["img"] = event["cover_img"] = event["original_img_name"] = "NONE"
#                 time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace(":", "_")
#                 file_name = f"{website}_{time_now}.xlsx"
                
#                 # for event in events:
#                 #     # run insert queries 
#                 #     pass
#                 await uploader.generate_xlsx(events=events, file_name=file_name)
#                 logging.info(f"Events fetched from {website} and XSLX uploaded successfully.")
#     except Exception:
#         logging.exception(f"An error occurred.")
#         print("An error occurred.")

# if __name__ == "__main__":
#     asyncio.run(main())

import os
import logging
import sys
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from datetime import datetime
import pandas as pd
import uuid
from args_parser import WEBSITE_FUNCTIONS, parse_arguments


# ---------------- FETCH EVENTS ---------------- #

async def fetch_events(website, city, days):
    try:
        events_fetch_function = WEBSITE_FUNCTIONS.get(website)

        if events_fetch_function is None:
            raise ValueError("Invalid website name.")

        print("Function being called:", events_fetch_function.__name__)

        # Sites using sync_playwright
        playwright_sites = {
            "meetup.com",
            "miamiandbeaches.com"
        }

        if website in playwright_sites:
            return await asyncio.to_thread(
                events_fetch_function,
                days=days,
                city=city.capitalize()
            )

        return events_fetch_function(
            city=city.capitalize(),
            days=days
        )

    except Exception:
        logging.exception("An error occurred while fetching events.")
        return []


# ---------------- DOWNLOAD IMAGE ---------------- #

async def download_image(session, url, img_dir):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                file_name = f"{uuid.uuid4().hex}.jpg"
                file_path = os.path.join(img_dir, file_name)

                with open(file_path, "wb") as f:
                    f.write(content)

                return file_path
            return "NONE"
    except Exception:
        return "NONE"


# ---------------- MAIN ---------------- #

async def main():
    try:
        parser, args = parse_arguments()

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        website = args.website
        city = args.city
        days = args.days

        events = await fetch_events(website, city, days)

        logging.info(f"Number of events found: {len(events)}")

        if not events:
            print("No events found.")
            return

        # Create folders
        today_folder = datetime.now().strftime("%Y-%m-%d")
        base_dir = os.path.join("scrap_results", today_folder)
        img_dir = os.path.join(base_dir, "images")
        report_dir = os.path.join(base_dir, "reports")

        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(report_dir, exist_ok=True)

        timeout = ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:

            tasks = []
            for event in events:
                url = event.get("original_img_name", "")
                if url and isinstance(url, str) and url.lower() != "none":
                    tasks.append(download_image(session, url, img_dir))
                else:
                    tasks.append(asyncio.sleep(0, result="NONE"))

            results = await asyncio.gather(*tasks)

            for event, img_path in zip(events, results):
                if img_path != "NONE":
                    event["img"] = event["cover_img"] = img_path
                else:
                    event["img"] = event["cover_img"] = "NONE"

        # ---------------- SAFE EXPORT ---------------- #

        MAX_URL_LENGTH = 2000
        save_as_csv = False

        for event in events:
            for key in ["event_url", "original_img_name"]:
                value = event.get(key)
                if isinstance(value, str) and len(value) > MAX_URL_LENGTH:
                    save_as_csv = True
                    break
            if save_as_csv:
                break

        df = pd.DataFrame(events)
        time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if save_as_csv:
            file_name = f"{website}_{time_now}.csv"
            file_path = os.path.join(report_dir, file_name)
            df.to_csv(file_path, index=False)
            print("\n⚠ Long URL detected → Saved as CSV")
        else:
            file_name = f"{website}_{time_now}.xlsx"
            file_path = os.path.join(report_dir, file_name)
            df.to_excel(file_path, index=False)
            print("\n✅ Saved as Excel")

        print(f"📁 File saved at: {file_path}")

    except Exception:
        logging.exception("An error occurred.")
        print("An error occurred.")


if __name__ == "__main__":
    asyncio.run(main())