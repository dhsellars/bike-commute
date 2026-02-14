from datetime import time

# --- LOCATION ---
LAT = 48.6850
LON = 9.0113
TIMEZONE = "Europe/Berlin"

# --- COMMUTE WINDOW ---
START_HOUR = 7
END_HOUR   = 19

# --- NOTIFICATION WINDOW ---
NOTIFY_END_HOUR = 17  # no updates after 17:00

# --- DRY CRITERIA ---
MAX_RAIN_MM = 0.0
MAX_POP = 20

# --- NTFY ---
NTFY_TOPIC = "bike-commute-d-48_68-9_01"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# --- STATE FILE ---
STATE_FILE = "state.json"
