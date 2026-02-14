import json
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    LAT, LON, TIMEZONE,
    START_HOUR, END_HOUR, NOTIFY_END_HOUR,
    MAX_RAIN_MM, MAX_POP,
    NTFY_URL, STATE_FILE
)

# --- WEATHER FETCHING ---

def fetch_hourly():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "rain,precipitation_probability,temperature_2m",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["hourly"]


# --- FIND DRY HOURS ---

def find_dry_hours(hourly):
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    times = hourly["time"]
    rains = hourly["rain"]
    pops = hourly["precipitation_probability"]
    temps_c = hourly["temperature_2m"]

    dry_hours = []

    for t_str, rain, pop, temp_c in zip(times, rains, pops, temps_c):
        dt = datetime.fromisoformat(t_str).replace(tzinfo=tz)

        # Only today
        if dt.date() != now.date():
            continue

        # Only within commute window
        if not (START_HOUR <= dt.hour <= END_HOUR):
            continue

        # Only future hours
        if dt <= now:
            continue

        # Dry criteria
        if rain <= MAX_RAIN_MM and pop <= MAX_POP:
            temp_f = temp_c * 9/5 + 32
            dry_hours.append({
                "time": dt.strftime("%H:%M"),
                "rain": rain,
                "pop": pop,
                "temp_f": round(temp_f)
            })

    return dry_hours


# --- STATE MANAGEMENT ---

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_notified_hours": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# --- NOTIFICATION ---

def notify(message: str):
    try:
        requests.post(NTFY_URL, data=message.encode("utf-8"))
    except Exception as e:
        print("Notification failed:", e)


# --- MAIN ---

def main():
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    hourly = fetch_hourly()
    dry_hours = find_dry_hours(hourly)

    # Convert to a simple list for state comparison
    dry_hour_strings = [h["time"] for h in dry_hours]

    state = load_state()
    last = state.get("last_notified_hours", [])

    # 7:00 → always send summary
    if now.hour == 7:
        if dry_hours:
            lines = [
                f"{h['time']} — {h['temp_f']}°F"
                for h in dry_hours
            ]
            msg = "Best dry travel hours today:\n" + "\n".join(lines)
        else:
            msg = "No dry travel hours today."

        notify(msg)
        state["last_notified_hours"] = dry_hour_strings
        save_state(state)
        return

    # After 17:00 → no updates
    if now.hour > NOTIFY_END_HOUR:
        return

    # During the day → only notify if changed
    if dry_hour_strings != last:
        if dry_hours:
            lines = [
                f"{h['time']} — {h['temp_f']}°F"
                for h in dry_hours
            ]
            msg = "Updated dry travel hours:\n" + "\n".join(lines)
        else:
            msg = "No remaining dry hours."

        notify(msg)
        state["last_notified_hours"] = dry_hour_strings
        save_state(state)
