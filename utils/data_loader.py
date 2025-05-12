import pandas as pd
import yaml

def load_yaml_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_weather_data(file_path):
    return pd.read_csv(file_path)