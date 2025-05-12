from models.pv_model import PVModel
from models.wind_model import WindModel
from utils.data_loader import load_weather_data

def create_generators(config):
    generators = []

    for pv_cfg in config.get("pv_systems", []):
        model = PVModel(**pv_cfg)
        weather = load_weather_data("data/" + pv_cfg["weather_file"])
        generators.append((model, weather))

    for wind_cfg in config.get("wind_systems", []):
        model = WindModel(**wind_cfg)
        weather = load_weather_data("data/" + wind_cfg["weather_file"])
        generators.append((model, weather))

    return generators

def run_simulation(generators):
    results = {}
    for model, weather in generators:
        power_output = [model.simulate_power(row) for _, row in weather.iterrows()]
        results[model.name] = power_output
    return results