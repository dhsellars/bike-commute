import os

# Secrets (in GitHub Actions)
LAT = float(os.environ["START_LAT"])
LON = float(os.environ["START_LON"])

TIMEZONE = os.environ["TIMEZONE"]

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# Public config (safe to commit)
START_HOUR = 7
END_HOUR = 18

MAX_RAIN_MM = 0.5
MAX_POP = 40


# Notification tuning
POP_DELTA_NOTIFY = 5          # percentage points
RAIN_DELTA_NOTIFY = 0.5       # mm
NOTIFY_ON_STATUS_CHANGE = True


STATE_FILE = f"state_{NTFY_TOPIC}.json"
