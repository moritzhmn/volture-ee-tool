from models.pv_model import PVModel
from models.wind_model import WindModel
from utils.data_loader import fetch_weather_from_api

def create_generators(config):
    generators = []

    for pv_cfg in config.get("pv_systems", []):
        model = PVModel(
            name=pv_cfg["name"],
            panel_angle_deg=pv_cfg["panel_angle_deg"],
            efficiency=pv_cfg["efficiency"],
            location=pv_cfg["location"]
        )
        weather = fetch_weather_from_api(
            lat=pv_cfg["location"]["lat"],
            lon=pv_cfg["location"]["lon"],
            date=pv_cfg["date"]
        )
        generators.append((model, weather))

    for wind_cfg in config.get("wind_systems", []):
        model = WindModel(
            name=wind_cfg["name"],
            rated_power=wind_cfg["rated_power"],
            cut_in=wind_cfg["cut_in"],
            cut_out=wind_cfg["cut_out"],
            rated_speed=wind_cfg["rated_speed"],
            location=wind_cfg["location"]
        )
        weather = fetch_weather_from_api(
            lat=wind_cfg["location"]["lat"],
            lon=wind_cfg["location"]["lon"],
            date=wind_cfg["date"]
        )
        generators.append((model, weather))

    return generators

def run_simulation(generators):
    results = {}
    for model, weather in generators:
        power_output = [model.simulate_power(row) for _, row in weather.iterrows()]
        results[model.name] = power_output
    return results