import requests
import yaml
import pandas as pd

def fetch_weather_from_api(lat, lon, date, timezone="Europe/Berlin", source="pv"):
    if source == "pv":
        url_ghi = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=shortwave_radiation"
            f"&start_date={date}&end_date={date}"
            f"&timezone={timezone}"
        )
        response_ghi = requests.get(url_ghi,timeout=10)
        data_ghi = response_ghi.json()
        ghi_data = data_ghi["hourly"]["shortwave_radiation"]
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

        # DataFrame erstellen
        timestamps = data_ghi["hourly"]["time"]
        df = pd.DataFrame({"time": pd.to_datetime(timestamps)})

        # Shortwave Radiation (GHI) und Temperatur hinzufügen
        df["GHI"] = ghi_data
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