import requests
import yaml
import pandas as pd

def fetch_weather_from_api(lat, lon, date, timezone="Europe/Berlin"):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=shortwave_radiation,wind_speed_10m"
        f"&start_date={date}&end_date={date}"
        f"&timezone={timezone}"
    )

    response = requests.get(url)
    data = response.json()

    timestamps = data["hourly"]["time"]
    irradiance = data["hourly"]["shortwave_radiation"]
    wind_speed = data["hourly"]["wind_speed_10m"]

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps),
        "irradiance": irradiance,
        "wind_speed": wind_speed
    })
    print(df)
    print(url)
    return df

def load_yaml_config(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)