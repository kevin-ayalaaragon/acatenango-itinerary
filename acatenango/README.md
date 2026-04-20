# Acatenango — Volcano Hike Itinerary App

A Django web app displaying an interactive itinerary for the Acatenango volcano hike in Guatemala.
Includes an interactive map, day-by-day timeline, trip poster, gear checklist, and live summit weather.

## Stack

| Layer | Tool |
|---|---|
| Backend | Django 4.2 |
| Frontend | Bootstrap 5 + Leaflet.js (map) + vanilla JS |
| Database | SQLite (no models needed — data is in `data.py`) |
| Static files | WhiteNoise |
| Hosting | Render |
| Web server | Gunicorn |
| Weather API | Open-Meteo (free, no API key required) |

## Local Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file
cp .env.example .env
# Edit .env if needed

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Run the development server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

## Weather Toggle

The live weather widget fetches current summit conditions from [Open-Meteo](https://open-meteo.com/) —
a free, no-key-required API.

**User-side toggle**: The toggle in the map section turns the widget on/off per-browser session
(saved in `localStorage`). The preference persists across page reloads.

**Server-side disable**: Set `WEATHER_ENABLED=False` in your environment variables to disable
the feature entirely (no API calls will be made server- or client-side).

The `/api/weather/` endpoint returns fresh JSON for the AJAX refresh button.

## Deployment on Render

1. Push to a GitHub repo
2. Create a new **Web Service** on Render, connecting your repo
3. Set **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
4. Set **Start Command**: `gunicorn acatenango.wsgi --bind 0.0.0.0:$PORT`
5. Add environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=your-domain.onrender.com`
6. Optionally add `WEATHER_ENABLED=False` to disable weather at the server level

## Customising the Itinerary

All trip data lives in `itinerary/data.py` — edit `STOPS`, `TIMELINE`, `GEAR`, and `STATS`
to adapt the app for any trek.
