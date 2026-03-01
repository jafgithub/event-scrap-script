import pathlib

import sys
import os

# CWD = pathlib.Path(__file__).cwd()
CWD = pathlib.Path(__file__).parent.resolve()

if sys.platform.startswith("win"):
    DRIVER_PATH = CWD / "drivers" / "chromedriver"  # Include .exe
else:
    DRIVER_PATH = "/home/ubuntu/events-scrap/chromedriver"

if not DRIVER_PATH.exists():
    raise FileNotFoundError(f"The driver path '{DRIVER_PATH}' does not exist.")

print(f"Using driver: {DRIVER_PATH}")

print(f"Using Chromedriver: {DRIVER_PATH}")

XPATH_DIR = CWD / 'xpath'

SERVICE_ACCOUNT_CREDS = CWD / 'file-scraping-983c52577b59.json'

if SERVICE_ACCOUNT_CREDS.exists():
    pass
else:
    raise FileNotFoundError(f"The service account credentials '{SERVICE_ACCOUNT_CREDS}' does not exist.")




# For 10times.com
AWS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

