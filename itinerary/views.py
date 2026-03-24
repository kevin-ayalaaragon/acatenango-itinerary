from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from .data import STOPS, TIMELINE, GEAR, STATS
from .weather import get_summit_weather


def index(request):
    """Main itinerary page — all sections in one view."""
    weather = None
    weather_enabled = getattr(settings, 'WEATHER_ENABLED', True)

    if weather_enabled:
        weather = get_summit_weather(
            settings.ACATENANGO_LAT,
            settings.ACATENANGO_LNG,
        )

    # Group timeline by day for template rendering
    days = {}
    for item in TIMELINE:
        days.setdefault(item["day"], []).append(item)

    context = {
        "stops": STOPS,
        "timeline_by_day": days,
        "gear": GEAR,
        "stats": STATS,
        "weather": weather,
        "weather_enabled": weather_enabled,
        "stops_json": _stops_json(STOPS),
    }
    return render(request, "itinerary/index.html", context)


def weather_api(request):
    """
    AJAX endpoint — returns fresh weather JSON.
    Called by the frontend toggle/refresh button.
    """
    if not getattr(settings, 'WEATHER_ENABLED', True):
        return JsonResponse({"enabled": False})

    data = get_summit_weather(
        settings.ACATENANGO_LAT,
        settings.ACATENANGO_LNG,
    )
    if data is None:
        return JsonResponse({"error": "Weather data unavailable"}, status=503)
    return JsonResponse({"enabled": True, "weather": data})


def _stops_json(stops):
    """Serialize stops to a JSON-safe list for the map JS."""
    import json
    return json.dumps([
        {
            "id": s["id"],
            "day": s["day"],
            "name": s["name"],
            "time": s["time"],
            "lat": s["lat"],
            "lng": s["lng"],
            "note": s["note"],
            "elevation": s["elevation"],
        }
        for s in stops
    ])
