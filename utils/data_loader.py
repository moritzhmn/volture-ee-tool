import requests
import yaml
import pandas as pd

def fetch_weather_from_api(lat, lon, date, tilt=None, azimuth=None, timezone="Europe/Berlin", source="pv"):
    if source == "pv":
        if tilt is None or azimuth is None:
         raise ValueError("Tilt und Azimuth müssen für PV-Daten angegeben werden")
    # Rest wie gehabt
        # GTI von Satellite API mit Neigung und Azimut
        url_gti = (
            f"https://satellite-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=global_tilted_irradiance_instant"
            f"&models=satellite_radiation_seamless"
            f"&tilt={tilt}&azimuth={azimuth}"
            f"&start_date={date}&end_date={date}"
            f"&timezone={timezone}"
        )
        print(url_gti)
        response_gti = requests.get(url_gti, timeout=10)
        data_gti = response_gti.json()
        gti_data = data_gti["hourly"]["global_tilted_irradiance_instant"]

        # Temperatur von Forecast API
        url_temp = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m"
            f"&start_date={date}&end_date={date}"
            f"&timezone={timezone}"
        )
        print(url_temp)
        response_temp = requests.get(url_temp, timeout=10)
        data_temp = response_temp.json()
        temp_data = data_temp["hourly"]["temperature_2m"]

        # Zeitstempel (aus GTI-Zeitreihe)
        timestamps = data_gti["hourly"]["time"]
        df = pd.DataFrame({"time": pd.to_datetime(timestamps)})

        # GTI und Temperatur einfügen
        df["GTI"] = gti_data
        df["temperature"] = temp_data

    elif source == "wind":
        url_wind = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=wind_speed_10m"
            f"&start_date={date}&end_date={date}"
            f"&timezone={timezone}"
        )
        response_wind = requests.get(url_wind, timeout=10)
        data_wind = response_wind.json()
        timestamps = data_wind["hourly"]["time"]
        df = pd.DataFrame({"time": pd.to_datetime(timestamps)})
        df["wind_speed"] = data_wind["hourly"]["wind_speed_10m"]
    else:
        raise ValueError("Unknown weather data source")

    return df

def load_yaml_config(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)