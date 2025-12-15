import math
import os
import pandas as pd
import streamlit as st


def explain_us_aqi(aqi: float) -> str:
    """Return human-friendly description for US AQI scale."""
    if aqi is None or (isinstance(aqi, float) and math.isnan(aqi)):
        return "AQI data not available."
    aqi = float(aqi)
    if aqi <= 50:
        return "Good – Air quality is considered satisfactory."
    elif aqi <= 100:
        return "Moderate – Acceptable; some pollutants may affect very sensitive people."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups – Sensitive people should reduce outdoor exertion."
    elif aqi <= 200:
        return "Unhealthy – Everyone may begin to feel adverse health effects."
    elif aqi <= 300:
        return "Very Unhealthy – Health alert; serious effects for everyone."
    else:
        return "Hazardous – Emergency conditions; avoid going outside."
    

def aqi_emoji(aqi: float) -> str:
    """Return a color emoji indicator for AQI level."""
    if aqi is None or (isinstance(aqi, float) and math.isnan(aqi)):
        return "⚪"   # unknown
    aqi = float(aqi)
    if aqi <= 50:
        return "🟢"  # Good
    elif aqi <= 100:
        return "🟡"  # Moderate
    elif aqi <= 150:
        return "🟠"  # Unhealthy for sensitive groups
    elif aqi <= 200:
        return "🔴"  # Unhealthy
    elif aqi <= 300:
        return "🟣"  # Very unhealthy
    else:
        return "⚫"  # Hazardous


def eco_tips(temp_c: float, weather_code: int, aqi: float, wind_speed: float):
    """Generate eco-friendly tips based on weather & AQI."""
    tips = []

    # Temperature
    if 18 <= temp_c <= 28:
        tips.append("🌡️ Comfortable temperature – use fans/natural airflow instead of AC to save energy.")
    elif temp_c > 30:
        tips.append("🥵 It’s hot – close curtains during the day & use light cotton clothes before lowering AC too much.")
    elif temp_c < 15:
        tips.append("🥶 It’s cool – wear extra layers instead of relying only on room heaters.")

    # Weather code categories (simplified)
    if weather_code in (0, 1):  # Clear, mainly clear
        tips.append("☀️ Clear sky – perfect to dry clothes outside instead of using a dryer.")
        tips.append("🔆 Use natural daylight instead of switching on lights.")
    elif weather_code in (2, 3):  # Partly cloudy / overcast
        tips.append("☁️ Cloudy – still enough daylight; keep unnecessary lights switched off.")
    elif 51 <= weather_code <= 67 or 80 <= weather_code <= 82:
        tips.append("🌧️ Rainy – collect some rainwater (where safe) for plants or cleaning.")
    elif 71 <= weather_code <= 77 or 85 <= weather_code <= 86:
        tips.append("❄️ Cold/wintry – ensure windows/doors are sealed to avoid heat loss.")

    # AQI & transport
    if aqi is not None and not (isinstance(aqi, float) and math.isnan(aqi)):
        aqi = float(aqi)
        if aqi > 150:
            tips.append("🚗 AQI is high – avoid using private vehicles; prefer public transport or carpooling.")
            tips.append("😷 Consider wearing a mask and avoid heavy outdoor exercise.")
        elif aqi <= 50:
            tips.append("🚶 AQI is good – great time to walk or cycle instead of using a vehicle.")

    # Wind
    if wind_speed is not None and wind_speed > 6:
        tips.append("💨 Windy outside – open windows for natural ventilation instead of running a fan all day.")

    if not tips:
        tips.append("✅ No special alerts – follow 3Rs: Reduce, Reuse, Recycle. ♻️")

    return tips


def pollutant_summary(pollutants: dict):
    """Return formatted text about key pollutants."""
    lines = []
    pm25 = pollutants.get("pm2_5")
    pm10 = pollutants.get("pm10")
    o3 = pollutants.get("ozone")
    no2 = pollutants.get("nitrogen_dioxide")
    co = pollutants.get("carbon_monoxide")

    if pm25 is not None:
        lines.append(f"PM2.5: {pm25:.1f} µg/m³")
    if pm10 is not None:
        lines.append(f"PM10: {pm10:.1f} µg/m³")
    if o3 is not None:
        lines.append(f"O₃ (ozone): {o3:.1f} µg/m³")
    if no2 is not None:
        lines.append(f"NO₂: {no2:.1f} µg/m³")
    if co is not None:
        lines.append(f"CO: {co:.1f} µg/m³")

    return "\n".join(lines) if lines else "Pollutant data not available."


def save_record_to_excel(record, file_path="weather_records.xlsx"):
    """Append a weather record row to Excel file (or create it)."""
    try:
        if os.path.exists(file_path):
            df_existing = pd.read_excel(file_path)
            df_new = pd.concat([df_existing, pd.DataFrame([record])], ignore_index=True)
            df_new.to_excel(file_path, index=False)
        else:
            pd.DataFrame([record]).to_excel(file_path, index=False)
    except Exception as e:
        st.warning(f"Could not save record to Excel: {e}")


def aqi_timeseries(aq_data: dict):
    """Convert hourly AQI data into a DataFrame for plotting line chart."""
    hourly = aq_data.get("hourly", {})
    times = hourly.get("time", [])
    aqi_values = hourly.get("us_aqi", [])
    if not times or not aqi_values:
        return None

    df = pd.DataFrame({
        "time": times,
        "US AQI": aqi_values
    })
    return df
