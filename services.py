import requests

# Open-Meteo endpoints (no API key required)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def geocode_city(city: str):
    """Use Open-Meteo geocoding to get latitude, longitude, country for a city name."""
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    r = requests.get(GEOCODE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = data.get("results")
    if not results:
        return None

    loc = results[0]
    return {
        "name": loc.get("name"),
        "country": loc.get("country"),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude")
    }


def get_weather_forecast(lat: float, lon: float):
    """Get current weather + 5-day forecast from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "weathercode"
        ],
        "timezone": "auto"
    }
    r = requests.get(FORECAST_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_air_quality(lat: float, lon: float):
    """Get air quality (including US AQI) from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["pm2_5", "pm10", "ozone", "nitrogen_dioxide", "carbon_monoxide", "us_aqi"],
        "timezone": "auto"
    }
    r = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def latest_aqi(aq_data: dict):
    """Extract the latest US AQI value and pollutants from air quality data."""
    hourly = aq_data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return None, {}

    idx = len(times) - 1

    aqi_values = hourly.get("us_aqi", [])
    aqi_val = aqi_values[idx] if idx < len(aqi_values) else None

    pollutants = {
        "pm2_5": _safe_get(hourly, "pm2_5", idx),
        "pm10": _safe_get(hourly, "pm10", idx),
        "ozone": _safe_get(hourly, "ozone", idx),
        "nitrogen_dioxide": _safe_get(hourly, "nitrogen_dioxide", idx),
        "carbon_monoxide": _safe_get(hourly, "carbon_monoxide", idx),
    }

    return aqi_val, pollutants


def _safe_get(hourly: dict, key: str, idx: int):
    arr = hourly.get(key)
    if not arr or idx >= len(arr):
        return None
    return arr[idx]
