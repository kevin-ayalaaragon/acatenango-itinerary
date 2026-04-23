from django.shortcuts import render
from datetime import date, datetime, timezone, timedelta
import zoneinfo
import json
from .data import STOPS, TIMELINE, GEAR, STATS

TRIP_START = date(2026, 4, 23)
TRIP_END   = date(2026, 4, 28)

DAY_DATES = {
    "Apr 23": date(2026, 4, 23),
    "Apr 24": date(2026, 4, 24),
    "Apr 25": date(2026, 4, 25),
    "Apr 26": date(2026, 4, 26),
    "Apr 27": date(2026, 4, 27),
    "Apr 28": date(2026, 4, 28),
}

GUATEMALA_TZ = zoneinfo.ZoneInfo("America/Guatemala")
ET_TZ        = zoneinfo.ZoneInfo("America/New_York")

# Key datetimes
DEPARTURE_DT = datetime(2026, 4, 23, 17, 52, 0, tzinfo=ET_TZ)        # IAD 5:52 PM ET
SUMMIT_DT    = datetime(2026, 4, 26,  5, 30, 0, tzinfo=GUATEMALA_TZ)  # Summit ~5:30 AM GT


def get_trip_status(today=None):
    now_utc = datetime.now(timezone.utc)

    if today:
        fake_now = datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=GUATEMALA_TZ)
        now_utc = fake_now.astimezone(timezone.utc)

    today_date = now_utc.astimezone(GUATEMALA_TZ).date()

    dep_utc    = DEPARTURE_DT.astimezone(timezone.utc)
    summit_utc = SUMMIT_DT.astimezone(timezone.utc)

    # ── BEFORE DEPARTURE — countdown to takeoff ──
    if now_utc < dep_utc:
        delta_days = (TRIP_START - today_date).days
        return {
            "trip_state": "before",
            "countdown_target": "departure",
            "countdown_label": "until departure",
            "days_until": max(0, delta_days),
            "today_label": None,
        }

    # ── AFTER TRIP ──
    if today_date > TRIP_END:
        return {
            "trip_state": "after",
            "days_since": (today_date - TRIP_END).days,
            "today_label": None,
            "countdown_target": None,
        }

    # ── DURING TRIP — before summit: countdown to summit ──
    if now_utc < summit_utc:
        today_label = next((lbl for lbl, d in DAY_DATES.items() if d == today_date), None)
        return {
            "trip_state": "during",
            "countdown_target": "summit",
            "countdown_label": "until the summit",
            "today_label": today_label,
        }

    # ── DURING TRIP — after summit ──
    today_label = next((lbl for lbl, d in DAY_DATES.items() if d == today_date), None)
    return {
        "trip_state": "during",
        "countdown_target": None,
        "today_label": today_label,
    }


def annotate_stops(stops, trip_status):
    today_label  = trip_status.get("today_label")
    trip_state   = trip_status["trip_state"]
    annotated    = []
    marked_today = False

    for stop in stops:
        s = dict(stop)
        if trip_state == "before":
            s["status"] = "upcoming"
        elif trip_state == "after":
            s["status"] = "done"
        else:
            stop_date  = DAY_DATES.get(stop["day"])
            today_date = DAY_DATES.get(today_label)
            if stop_date and today_date:
                if stop_date < today_date:
                    s["status"] = "done"
                elif stop_date == today_date and not marked_today:
                    s["status"] = "today"
                    marked_today = True
                else:
                    s["status"] = "upcoming"
            else:
                s["status"] = "upcoming"
        annotated.append(s)
    return annotated


def annotate_timeline(timeline_by_day, trip_status):
    today_label = trip_status.get("today_label")
    trip_state  = trip_status["trip_state"]
    today_date  = DAY_DATES.get(today_label) if today_label else None
    annotated   = {}

    for day_label, items in timeline_by_day.items():
        date_part = day_label.split(" — ")[0]
        day_date  = DAY_DATES.get(date_part)

        if trip_state == "before":
            status = "upcoming"
        elif trip_state == "after":
            status = "done"
        elif today_date and day_date:
            if day_date < today_date:
                status = "done"
            elif day_date == today_date:
                status = "today"
            else:
                status = "upcoming"
        else:
            status = "upcoming"

        annotated[day_label] = {"items": items, "status": status}
    return annotated


def index(request):
    test_date = None
    raw = request.GET.get('date')
    if raw:
        try:
            test_date = datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass

    trip_status = get_trip_status(today=test_date)

    days = {}
    for item in TIMELINE:
        days.setdefault(item["day"], []).append(item)

    annotated_stops    = annotate_stops(STOPS, trip_status)
    annotated_timeline = annotate_timeline(days, trip_status)

    context = {
        "stops": annotated_stops,
        "timeline_by_day": annotated_timeline,
        "gear": GEAR,
        "stats": STATS,
        "trip_status": trip_status,
        "stops_json": _stops_json(annotated_stops),
    }
    return render(request, "itinerary/index.html", context)


def _stops_json(stops):
    return json.dumps([
        {
            "id": s["id"], "day": s["day"], "name": s["name"],
            "time": s["time"], "lat": s["lat"], "lng": s["lng"],
            "note": s["note"], "elevation": s["elevation"],
            "status": s.get("status", "upcoming"),
        }
        for s in stops
    ])
