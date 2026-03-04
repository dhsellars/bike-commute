import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional  # <-- add this
from config import (
    LAT, LON,
    TIMEZONE, START_HOUR, END_HOUR,
    MAX_RAIN_MM, MAX_POP,
    POP_DELTA_NOTIFY, RAIN_DELTA_NOTIFY, NOTIFY_ON_STATUS_CHANGE,
    NTFY_URL, STATE_FILE
)

# --------------------------------------------
# State helpers
# --------------------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_notification": None, "last_snapshot": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# --------------------------------------------
# Notify
# --------------------------------------------
def notify(message):
    try:
        requests.post(NTFY_URL, data=message.encode("utf-8"), timeout=10)
    except Exception:
        pass


# --------------------------------------------
# Weather fetch
# --------------------------------------------
def get_weather_localtime():
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "precipitation,precipitation_probability,temperature_2m",
        "forecast_days": 2,
        "timezone": TIMEZONE,
    }
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# --------------------------------------------
# Time helpers
# --------------------------------------------
def next_occurrence_of_hour(now_local: datetime, hour: int) -> datetime:
    candidate = now_local.replace(hour=hour, minute=0, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)
    return candidate


def build_local_dt_index(weather_json, tz: str):
    times = weather_json["hourly"]["time"]
    rain = weather_json["hourly"]["precipitation"]
    pop = weather_json["hourly"]["precipitation_probability"]
    temp = weather_json["hourly"]["temperature_2m"]

    z = ZoneInfo(tz)
    idx = {}
    for t, r_mm, p, t_c in zip(times, rain, pop, temp):
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt_local = dt.replace(tzinfo=z)
        else:
            dt_local = dt.astimezone(z)
        idx[dt_local] = (float(r_mm), int(p), float(t_c))
    return idx


# --------------------------------------------
# Status + snapshot
# --------------------------------------------
def classify(r_mm: float, p: int) -> str:
    if r_mm <= MAX_RAIN_MM and p <= MAX_POP:
        return "🟢 good"
    elif r_mm <= MAX_RAIN_MM * 2 and p <= MAX_POP * 2:
        return "🟡 meh"
    else:
        return "🔴 nope"


def format_status(status: str, word_width: int = 6) -> str:
    parts = status.split(" ", 1)
    if len(parts) == 2:
        emoji, word = parts
    else:
        emoji, word = "", status

    padded_word = word.ljust(word_width)
    return f"{emoji} {padded_word}"


def make_snapshot(now_local: datetime, idx: dict) -> dict:
    hours_map = {}
    tz = ZoneInfo(TIMEZONE)

    for h in range(START_HOUR, END_HOUR + 1):
        target_dt = next_occurrence_of_hour(now_local, h).astimezone(tz)
        vals = idx.get(target_dt)
        if vals is None:
            continue

        r_mm, p, t_c = vals
        status = classify(r_mm, p)

        hours_map[f"{h:02}"] = {
            "iso": target_dt.strftime("%m.%dT%H:%M"),
            "dow": target_dt.strftime("%a"),
            "r_mm": round(r_mm, 1),
            "pop": int(p),
            "temp_c": round(t_c, 1),
            "status": status,
        }

    return {"hours": hours_map}


def should_notify(prev_snapshot: Optional[dict], new_snapshot: dict) -> bool:
    if not prev_snapshot:
        return True

    prev_hours = prev_snapshot.get("hours", {}) or {}
    new_hours = new_snapshot.get("hours", {}) or {}

    if set(prev_hours.keys()) != set(new_hours.keys()):
        return True

    for h in new_hours:
        p = prev_hours.get(h)
        n = new_hours[h]
        if p is None:
            return True

        if NOTIFY_ON_STATUS_CHANGE and p["status"] != n["status"]:
            return True

        if abs(n["pop"] - p["pop"]) >= POP_DELTA_NOTIFY:
            return True

        if abs(n["r_mm"] - p["r_mm"]) >= RAIN_DELTA_NOTIFY:
            return True

    return False


def hour_label(h: int) -> str:
    if h == 0:
        label = "12am"
    elif 1 <= h < 12:
        label = f"{h}am"
    elif h == 12:
        label = "12pm"
    else:
        label = f"{h-12}pm"

    return label.ljust(4)


# --------------------------------------------
# Main
# --------------------------------------------
def main():
    state = load_state()
    now_local = datetime.now(ZoneInfo(TIMEZONE))

    weather = get_weather_localtime()
    dt_index = build_local_dt_index(weather, TIMEZONE)

    snapshot = make_snapshot(now_local, dt_index)

    hours_list = []
    good = borderline = bad = 0

    for h in sorted(snapshot["hours"].keys()):
        entry = snapshot["hours"][h]
        status = entry["status"]
        status_fixed = format_status(status, word_width=6)

        r_mm = entry["r_mm"]
        p = entry["pop"]
        t_c = entry["temp_c"]
        t_f = (t_c * 9/5) + 32
        dow = entry["dow"]

        if status.startswith("🟢"):
            good += 1
        elif status.startswith("🟡"):
            borderline += 1
        else:
            bad += 1

        hours_list.append(
            f"{hour_label(int(h))} {status_fixed} ({r_mm:4.1f},{p:3d}%, {t_f:4.0f}°F) [{dow}]"
        )

    if good == 0 and borderline == 0:
        summary = "🚫 No good travel times."
    elif good > 0 and bad == 0:
        summary = "✨ All good all day!"
    elif good > 0:
        summary = "🌤️ Mostly good conditions."
    elif borderline > 0:
        summary = "🌦️ Mixed conditions — choose wisely."
    else:
        summary = "🌧️ Rain likely."

    message = summary + "\n\nNext occurrences for {:02}:00–{:02}:00:\n{}".format(
        START_HOUR,
        END_HOUR,
        "\n".join(hours_list) if hours_list else "(none available)"
    )

    if should_notify(state.get("last_snapshot"), snapshot):
        notify(message)
        state["last_notification"] = message
        state["last_snapshot"] = snapshot
        save_state(state)


if __name__ == "__main__":
    main()
