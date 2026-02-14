from datetime import time

# --- LOCATION ---
LAT = 48.6850
LON = 9.0113
TIMEZONE = "Europe/Berlin"

# --- COMMUTE WINDOW ---
# You can travel any time between these hours
EARLIEST = time(7, 0)
LATEST   = time(17, 0)

# --- DRY CRITERIA ---
MAX_RAIN_MM = 0.0
MAX_POP = 20  # precipitation probability %

# --- NOTIFICATION ---
# Pick any random-ish topic name
NTFY_TOPIC = "bike-commute-d-48_68-9_01"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
