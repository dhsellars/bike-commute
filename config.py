from datetime import time
import os
from dotenv import load_dotenv

load_dotenv()

LAT = float(os.getenv("LAT"))
LON = float(os.getenv("LON"))
TIMEZONE = os.getenv("TIMEZONE")

START_HOUR = int(os.getenv("START_HOUR"))
END_HOUR = int(os.getenv("END_HOUR"))
NOTIFY_END_HOUR = int(os.getenv("NOTIFY_END_HOUR"))

MAX_RAIN_MM = float(os.getenv("MAX_RAIN_MM"))
MAX_POP = int(os.getenv("MAX_POP"))

NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

STATE_FILE = f"state_{NTFY_TOPIC}.json"
