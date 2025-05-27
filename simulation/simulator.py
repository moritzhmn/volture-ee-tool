from models.pv_model import PVModel
from models.wind_model import WindModel
from utils.data_loader import fetch_weather_from_api

def create_generators(config):
    generators = []

    for pv_cfg in config.get("pv_systems", []):
        model = PVModel(
            name=pv_cfg["name"],
            rated_power=pv_cfg["rated_power"],
            age=pv_cfg["age"],
            shading=pv_cfg["shading"],
            albedo=pv_cfg["albedo"],
            azimuth=pv_cfg["azimuth"],
            D_soil=pv_cfg["D_soil"],
            tilt=pv_cfg["tilt"],
            size=pv_cfg["size"],
            location=(pv_cfg["location"]["lat"], pv_cfg["location"]["lon"])
        )
        weather = fetch_weather_from_api(
            lat=pv_cfg["location"]["lat"],
            lon=pv_cfg["location"]["lon"],
            tilt=pv_cfg["tilt"],
            azimuth=pv_cfg["azimuth"],
            date=pv_cfg["date"],
            source="pv"
        )
        generators.append((model, weather))

    for wind_cfg in config.get("wind_systems", []):
        wind_model = WindModel(
            name=wind_cfg["name"],
            rated_power=wind_cfg["rated_power"],
            rotor_radius=wind_cfg["rotor_radius"],
            hub_height=wind_cfg["hub_height"],
            cut_in=wind_cfg["cut_in"],
            rated_speed=wind_cfg["rated_speed"],
            cut_out=wind_cfg["cut_out"],
            alpha=wind_cfg.get("alpha", 0.2),
            wake_loss=wind_cfg.get("wake_loss", 0.1),
            location=wind_cfg["location"],
            turbines_count=wind_cfg["turbines"]
        )
        weather = fetch_weather_from_api(
            lat=wind_cfg["location"]["lat"],
            lon=wind_cfg["location"]["lon"],
            date=wind_cfg["date"],
            source="wind"
        )
        generators.append((wind_model, weather))

    return generators

def run_simulation(generators):
    results = {}
    for model, weather in generators:
        power_output = [model.simulate_power(row) for _, row in weather.iterrows()]
        results[model.name] = power_output
    return results