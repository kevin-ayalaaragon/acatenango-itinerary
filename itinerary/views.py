from django.shortcuts import render
from datetime import date, datetime
import zoneinfo
import json
from .data import STOPS, TIMELINE, GEAR, STATS

# ── TRIP DATES (2026) ──────────────────────────────────────────
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


def get_today():
    return datetime.now(GUATEMALA_TZ).date()


def get_trip_status(today=None):
    today = today or get_today()
    if today < TRIP_START:
        delta = (TRIP_START - today).days
        return {
            "trip_state": "before",
            "days_until": delta,
            "today_label": None,
            "countdown": f"{delta} day{'s' if delta != 1 else ''} until departure",
        }
    elif today > TRIP_END:
        return {
            "trip_state": "after",
            "days_since": (today - TRIP_END).days,
            "today_label": None,
            "countdown": None,
        }
    else:
        today_label = next((lbl for lbl, d in DAY_DATES.items() if d == today), None)
        return {
            "trip_state": "during",
            "today_label": today_label,
            "days_until": None,
            "countdown": None,
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
    # Allow ?date=YYYY-MM-DD for testing
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
        "stops_json": json.dumps([
            {
                "id": s["id"], "day": s["day"], "name": s["name"],
                "time": s["time"], "lat": s["lat"], "lng": s["lng"],
                "note": s["note"], "elevation": s["elevation"],
                "status": s.get("status", "upcoming"),
            }
            for s in annotated_stops
        ]),
    }
    return render(request, "itinerary/index.html", context)
