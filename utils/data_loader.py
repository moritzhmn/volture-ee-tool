import requests
import pandas as pd
from datetime import datetime, timedelta
import yaml


def load_yaml_config(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)

# Mapping von internen Namen auf Energy-Charts-Stationen
LOCATION_MAP = {
    "Dresden": "Dresden-Klotzsche",
    "Saarbruecken": "Saarbrücken-Ensheim",
    "Giessen": "Gießen/Wettenberg",
    "Wuerzburg": "Würzburg",
    "Bremen": "Bremen"
}

def load_weather_data(location, date, typ):
    # Datum verarbeiten
    target_date = pd.to_datetime(date).date()
    year = target_date.year
    month = target_date.month

    # Standort-Mapping
    mapped_location = LOCATION_MAP.get(location, location)

    # Typ-spezifischer Teil für URL und Rückgabe-Key
    if typ == "pv":
        data_type = "solar_globe"
        typ_key = "pv"
    elif typ == "wind":
        data_type = "wind_speed"
        typ_key = "wind"
    else:
        raise ValueError(f"Unbekannter Typ '{typ}'")

    # Baue die URL
    url = f"https://www.energy-charts.info/charts/climate_hours/data/de/month_{data_type}_{year}_{month:02d}.json"

    # JSON laden
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"❌ Fehler beim Abrufen von Wetterdaten: {e}")

    data = response.json()

    # Standortdaten finden
    station = next((s for s in data if s["name"] == mapped_location), None)
    if station is None:
        raise ValueError(f"⚠️ Standort '{mapped_location}' nicht in JSON-Daten enthalten.")

    values = station["data"]
    start_dt = datetime(year, month, 1)

    # Erzeuge Liste mit datetime und Wert (alle Stunden des Monats)
    full_series = [
        {"datetime": start_dt + timedelta(hours=i), typ_key: val if val is not None else 0}
        for i, val in enumerate(values)
    ]

    # Filter auf gewünschtes Datum
    filtered = [entry for entry in full_series if entry["datetime"].date() == target_date]
    if not filtered:
        raise ValueError(f"⚠️ Keine Wetterdaten für {mapped_location} am {date} vorhanden.")

    return filtered