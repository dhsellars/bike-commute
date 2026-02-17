import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import (
    START_LAT, START_LON, END_LAT, END_LON,
    TIMEZONE, START_HOUR, END_HOUR,
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
    requests.post(NTFY_URL, data=message.encode("utf-8"))

def get_tomorrow_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={START_LAT}&longitude={START_LON}"
        "&hourly=precipitation,precipitation_probability"
        "&forecast_days=2"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    state = load_state()
    now = datetime.now(ZoneInfo(TIMEZONE))

    # Determine tomorrow's date
    tomorrow = (now + timedelta(days=1)).date()

    weather = get_tomorrow_weather()
    hours = weather["hourly"]["time"]
    rain = weather["hourly"]["precipitation"]
    pop = weather["hourly"]["precipitation_probability"]

    results = []
    good_count = 0
    borderline_count = 0
    bad_count = 0

    for t, r_mm, p in zip(hours, rain, pop):
        dt = datetime.fromisoformat(t).replace(tzinfo=ZoneInfo(TIMEZONE))

        if dt.date() != tomorrow:
            continue

        if START_HOUR <= dt.hour <= END_HOUR:
            if r_mm <= MAX_RAIN_MM and p <= MAX_POP:
                status = "🟢 good"
                good_count += 1
            elif r_mm <= MAX_RAIN_MM * 2 and p <= MAX_POP * 2:
                status = "🟡 borderline"
                borderline_count += 1
            else:
                status = "🔴 not recommended"
                bad_count += 1

            results.append(f"{dt.hour:02}:00 — {status} ({r_mm}mm, {p}%)")

    # Build summary line
    if good_count == 0 and borderline_count == 0:
        summary = "🚫 No good commute windows tomorrow."
    elif good_count > 0 and bad_count == 0:
        summary = "✨ All commute hours tomorrow look great!"
    elif good_count > 0:
        summary = "🌤️ Tomorrow looks mostly good for biking!"
    elif borderline_count > 0:
        summary = "🌦️ Mixed conditions tomorrow — choose your hour wisely."
    else:
        summary = "🌧️ Tomorrow looks rainy — biking may not be ideal."

    # Build final message
    if results:
        message = summary + "\n\nBike commute forecast for tomorrow:\n" + "\n".join(results)
    else:
        message = summary

    # Avoid duplicate notifications
    if state.get("last_notification") != message:
        notify(message)
        state["last_notification"] = message
        save_state(state)

if __name__ == "__main__":
    main()
