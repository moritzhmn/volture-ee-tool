from utils.data_loader import load_yaml_config
from simulation.simulator import create_generators, run_simulation

config = load_yaml_config("config.yaml")
generators = create_generators(config)
results = run_simulation(generators)

for name, power_series in results.items():
    print(f"{name}: {power_series[:5]} ...")