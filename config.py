import os

# Secrets (from GitHub Actions)
START_LAT = float(os.environ["START_LAT"])
START_LON = float(os.environ["START_LON"])
END_LAT = float(os.environ["END_LAT"])
END_LON = float(os.environ["END_LON"])

TIMEZONE = os.environ["TIMEZONE"]

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# Public config (safe to commit)
START_HOUR = 6
END_HOUR = 10
NOTIFY_END_HOUR = 9

MAX_RAIN_MM = 0.5
MAX_POP = 30

STATE_FILE = f"state_{NTFY_TOPIC}.json"
