import streamlit as st
from datetime import datetime
import math
import pandas as pd

from services import geocode_city, get_weather_forecast, get_air_quality, latest_aqi
from helpers import (
    explain_us_aqi,
    eco_tips,
    pollutant_summary,
    save_record_to_excel,
    aqi_timeseries,
    aqi_emoji,
)


st.set_page_config(
    page_title="Eco Weather + AQI Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Eco Weather + AQI Dashboard (Open-Meteo, No API Key)")
st.caption("Current weather, 5-day forecast, air quality (US AQI), eco-friendly suggestions & Excel logging.")


# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    city = st.text_input("Enter city name", value="Delhi")

    units = st.radio("Temperature unit", ["Celsius", "Fahrenheit"], index=0)

    show_raw = st.checkbox("Show raw API data (geek mode)", value=False)

    st.markdown("---")
    st.markdown("**Powered by Open-Meteo Weather & Air Quality (no API key needed)**")


# Main logic
if st.button("🔍 Get Eco Weather"):
    if not city.strip():
        st.error("Please enter a city name.")
    else:
        # ---------- GEOCODING ----------
        try:
            location = geocode_city(city.strip())
        except Exception as e:
            st.error(f"Error geocoding city: {e}")
            st.stop()

        if not location:
            st.error("Could not find this city. Try a different spelling or include country (e.g., 'Delhi, India').")
            st.stop()

        lat = location["latitude"]
        lon = location["longitude"]
        city_name = location["name"]
        country = location["country"]

        # ---------- WEATHER FORECAST ----------
        try:
            weather_data = get_weather_forecast(lat, lon)
        except Exception as e:
            st.error(f"Error fetching weather data: {e}")
            st.stop()

        current = weather_data.get("current_weather", {})
        daily = weather_data.get("daily", {})

        temp_c = current.get("temperature")
        wind_speed = current.get("windspeed")
        weather_code = current.get("weathercode")
        time_str = current.get("time")

        # Unit conversion
        if units == "Fahrenheit" and temp_c is not None:
            temp = temp_c * 9/5 + 32
            temp_unit = "°F"
        else:
            temp = temp_c
            temp_unit = "°C"

        # ---------- AIR QUALITY ----------
        aqi_val, pollutants, aqi_df = None, {}, None
        try:
            aq_data = get_air_quality(lat, lon)
            aqi_val, pollutants = latest_aqi(aq_data)
            aqi_df = aqi_timeseries(aq_data)
        except Exception:
            aqi_val, pollutants, aqi_df = None, {}, None

        # ---------- SAVE TO EXCEL ----------
        record = {
            "Date & Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "City": city_name,
            "Country": country,
            "Temperature (°C)": temp_c,
            "Wind Speed (km/h)": wind_speed,
            "Weather Code": weather_code,
            "US AQI": aqi_val
        }
        save_record_to_excel(record)
        st.success("📊 Weather record saved in 'weather_records.xlsx'")

        # ---------- LAYOUT: CURRENT INFO ----------
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📍 Location")
            st.metric("City", f"{city_name}, {country}")
            if time_str:
                st.caption(f"Updated at: {time_str} (local time)")

        with col2:
            st.subheader("🌡️ Temperature")
            if temp is not None:
                st.metric("Current", f"{temp:.1f}{temp_unit}")
            else:
                st.metric("Current", "N/A")
            st.metric("Humidity", "N/A")  # can be extended with hourly humidity

        with col3:
            st.subheader("🌬️ Wind")
            if wind_speed is not None:
                st.metric("Wind Speed", f"{wind_speed:.1f} km/h")
            else:
                st.metric("Wind Speed", "N/A")
            st.metric("Weather Code", str(weather_code) if weather_code is not None else "N/A")

        st.markdown("---")

        # ---------- AIR QUALITY SECTION ----------
        st.subheader("😷 Air Quality (US AQI)")
        if aqi_val is not None and not (isinstance(aqi_val, float) and math.isnan(aqi_val)):
            badge = aqi_emoji(aqi_val)
            st.write(f"{badge} **US AQI:** {aqi_val:.0f}")
            st.info(explain_us_aqi(aqi_val))
            st.text("Key pollutants:")
            st.text(pollutant_summary(pollutants))

            # AQI line chart (hourly)
            if aqi_df is not None and not aqi_df.empty:
                st.markdown("**AQI Trend (recent hours)**")
                aqi_df_plot = aqi_df.copy()
                aqi_df_plot["time"] = pd.to_datetime(aqi_df_plot["time"])
                aqi_df_plot = aqi_df_plot.set_index("time")
                st.line_chart(aqi_df_plot["US AQI"])
        else:
            st.warning("Air quality data not available for this location.")

        st.markdown("---")

        # ---------- FORECAST SECTION (UP TO 5 DAYS) ----------
        st.subheader("📅 5-Day Forecast (Daily Min/Max from Open-Meteo)")
        dates = daily.get("time", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        wcodes = daily.get("weathercode", [])

        num_days = min(5, len(dates))
        if num_days == 0:
            st.warning("Forecast data not available.")
        else:
            cols = st.columns(num_days)
            for i in range(num_days):
                with cols[i]:
                    date_str = dates[i]
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        label = date_obj.strftime("%a, %d %b")
                    except Exception:
                        label = date_str

                    st.markdown(f"**{label}**")

                    d_tmax = tmax[i] if i < len(tmax) else None
                    d_tmin = tmin[i] if i < len(tmin) else None
                    d_code = wcodes[i] if i < len(wcodes) else None

                    if units == "Fahrenheit":
                        if d_tmax is not None:
                            d_tmax = d_tmax * 9/5 + 32
                        if d_tmin is not None:
                            d_tmin = d_tmin * 9/5 + 32

                    if d_tmin is not None:
                        st.write(f"Min: {d_tmin:.1f}{temp_unit}")
                    if d_tmax is not None:
                        st.write(f"Max: {d_tmax:.1f}{temp_unit}")
                    st.write(f"Weather code: {d_code}")

        st.markdown("---")

        # ---------- ECO TIPS ----------
        st.subheader("🌱 Eco-Friendly Suggestions")
        tips = eco_tips(temp_c if temp_c is not None else 25.0,
                        weather_code if weather_code is not None else 1,
                        aqi_val,
                        wind_speed if wind_speed is not None else 0.0)
        for tip in tips:
            st.write("• " + tip)

        # ---------- RAW JSON ----------
        if show_raw:
            st.markdown("---")
            st.subheader("🧾 Raw API Data")
            with st.expander("Geocoding JSON"):
                st.json(location)
            with st.expander("Weather JSON"):
                st.json(weather_data)
            with st.expander("Air Quality JSON"):
                st.json(aq_data if 'aq_data' in locals() else {})
