import pathlib
import sys
import os

CWD = pathlib.Path(__file__).parent.resolve()

if sys.platform.startswith("win"):
    DRIVER_PATH = CWD / "drivers" / "chromedriver.exe"
else:
    DRIVER_PATH = CWD / "drivers" / "chromedriver"

# Windows: auto install if not exists
if sys.platform.startswith("win") and not DRIVER_PATH.exists():
    print("Chromedriver not found. Installing automatically...")

    from webdriver_manager.chrome import ChromeDriverManager
    from shutil import copyfile
    import os

    driver_downloaded_path = ChromeDriverManager().install()

    os.makedirs(CWD / "drivers", exist_ok=True)
    copyfile(driver_downloaded_path, DRIVER_PATH)

# Linux / EC2: must exist
if not DRIVER_PATH.exists():
    raise FileNotFoundError(f"The driver path '{DRIVER_PATH}' does not exist.")

print(f"Using driver: {DRIVER_PATH}")

XPATH_DIR = CWD / 'xpath'
SERVICE_ACCOUNT_CREDS = CWD / 'file-scraping-983c52577b59.json'

AWS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
