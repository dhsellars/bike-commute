import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    LAT, LON, TIMEZONE,
    EARLIEST, LATEST,
    MAX_RAIN_MM, MAX_POP,
    NTFY_URL
)

# --- WEATHER FETCHING ---

def fetch_hourly():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "rain,precipitation_probability",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["hourly"]


# --- FILTERING LOGIC ---

def find_dry_windows(hourly):
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    times = hourly["time"]
    rains = hourly["rain"]
    pops = hourly["precipitation_probability"]

    candidates = []

    for t_str, rain, pop in zip(times, rains, pops):
        dt = datetime.fromisoformat(t_str).replace(tzinfo=tz)

        # Only future times
        if dt <= now:
            continue

        # Only within your allowed travel window
        if not (EARLIEST <= dt.time() <= LATEST):
            continue

        # Dry criteria
        if rain <= MAX_RAIN_MM and pop <= MAX_POP:
            candidates.append((dt, rain, pop))

    return candidates


# --- NOTIFICATION ---

def notify(message: str):
    try:
        requests.post(NTFY_URL, data=message.encode("utf-8"))
    except Exception as e:
        print("Notification failed:", e)


# --- MAIN ---

def main():
    hourly = fetch_hourly()
    dry = find_dry_windows(hourly)

    if not dry:
        notify("No dry travel windows found in the next hours.")
        return

    lines = [
        f"{dt.strftime('%H:%M')}  rain={rain:.2f}mm  pop={pop}%"
        for dt, rain, pop in dry
    ]

    msg = "Dry travel windows:\n" + "\n".join(lines)
    notify(msg)


if __name__ == "__main__":
    main()
