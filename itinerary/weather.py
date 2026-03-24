"""
Weather service using the free Open-Meteo API — no API key required.
Fetches current conditions at the Acatenango summit coordinates.
"""
import urllib.request
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lng}"
    "&current=temperature_2m,apparent_temperature,precipitation,wind_speed_10m,"
    "wind_gusts_10m,cloud_cover,visibility,weather_code"
    "&wind_speed_unit=kmh&timezone=America/Guatemala"
)

WMO_DESCRIPTIONS = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Light showers", "🌦️"),
    81: ("Showers", "🌧️"),
    82: ("Heavy showers", "⛈️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm + hail", "⛈️"),
    99: ("Thunderstorm + heavy hail", "⛈️"),
}

def get_summit_weather(lat: float, lng: float) -> dict | None:
    """
    Fetch current weather at the given coordinates.
    Returns a dict of weather data or None on failure.
    """
    url = OPEN_METEO_URL.format(lat=lat, lng=lng)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "acatenango-itinerary/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        current = data.get("current", {})
        code = current.get("weather_code", 0)
        desc, emoji = WMO_DESCRIPTIONS.get(code, ("Unknown", "🌡️"))

        temp_c = current.get("temperature_2m")
        apparent_c = current.get("apparent_temperature")
        wind_kmh = current.get("wind_speed_10m")
        gusts_kmh = current.get("wind_gusts_10m")
        cloud_pct = current.get("cloud_cover")
        precip_mm = current.get("precipitation")
        visibility_m = current.get("visibility")

        return {
            "temp_c": round(temp_c, 1) if temp_c is not None else None,
            "apparent_c": round(apparent_c, 1) if apparent_c is not None else None,
            "wind_kmh": round(wind_kmh) if wind_kmh is not None else None,
            "gusts_kmh": round(gusts_kmh) if gusts_kmh is not None else None,
            "cloud_pct": round(cloud_pct) if cloud_pct is not None else None,
            "precip_mm": round(precip_mm, 1) if precip_mm is not None else None,
            "visibility_km": round(visibility_m / 1000, 1) if visibility_m is not None else None,
            "description": desc,
            "emoji": emoji,
            "code": code,
            "fetched_at": datetime.now().strftime("%H:%M"),
            "hiking_advisory": _hiking_advisory(temp_c, wind_kmh, code),
        }
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return None


def _hiking_advisory(temp_c, wind_kmh, code):
    """Return a simple hiking safety advisory based on conditions."""
    if temp_c is None or wind_kmh is None:
        return None
    issues = []
    if temp_c < -5:
        issues.append("Extreme cold — extra insulation essential")
    elif temp_c < 2:
        issues.append("Very cold at the summit — dress in full layers")
    if wind_kmh > 60:
        issues.append("Dangerous wind speeds — summit may be unsafe")
    elif wind_kmh > 40:
        issues.append("Strong winds expected — secure all gear")
    if code in (71, 73, 75, 77, 85, 86):
        issues.append("Snow on trail — traction devices recommended")
    if code in (95, 96, 99):
        issues.append("Thunderstorm active — do not attempt summit")
    if not issues:
        if temp_c > 5 and wind_kmh < 30 and code < 50:
            return {"level": "good", "text": "Conditions look favourable for hiking"}
        return {"level": "ok", "text": "Conditions acceptable — standard precautions apply"}
    return {"level": "warn", "text": " · ".join(issues)}
