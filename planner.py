import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import (
    START_LAT, START_LON, END_LAT, END_LON,
    TIMEZONE, START_HOUR, END_HOUR, NOTIFY_END_HOUR,
    MAX_RAIN_MM, MAX_POP, NTFY_URL, STATE_FILE
)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_notification": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def notify(message):
    requests.post(NTFY_URL, json={"message": message})

def get_weather():
    # Example using Open-Meteo (no API key required)
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={START_LAT}&longitude={START_LON}"
        "&hourly=precipitation,precipitation_probability"
        "&forecast_days=1"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    state = load_state()
    now = datetime.now(ZoneInfo(TIMEZONE))

    if now.hour < START_HOUR or now.hour > NOTIFY_END_HOUR:
        return

    weather = get_weather()
    hours = weather["hourly"]["time"]
    rain = weather["hourly"]["precipitation"]
    pop = weather["hourly"]["precipitation_probability"]

    # Find the next commute window hour
    for t, r_mm, p in zip(hours, rain, pop):
        dt = datetime.fromisoformat(t).replace(tzinfo=ZoneInfo(TIMEZONE))
        if START_HOUR <= dt.hour <= END_HOUR:
            if r_mm <= MAX_RAIN_MM and p <= MAX_POP:
                message = f"Good time to bike: {dt.hour}:00 — rain {r_mm}mm, pop {p}%"
            else:
                message = f"Not ideal: {dt.hour}:00 — rain {r_mm}mm, pop {p}%"

            if state.get("last_notification") != message:
                notify(message)
                state["last_notification"] = message
                save_state(state)
            break

if __name__ == "__main__":
    main()
