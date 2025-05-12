from utils.data_loader import load_yaml_config
from simulation.simulator import create_generators, run_simulation

config = load_yaml_config("config.yaml")
generators = create_generators(config)
results = run_simulation(generators)

# Strukturierte Ausgabe der Ergebnisse
for model_name, power_output in results.items():
    print(f"Ergebnisse für {model_name}:")
    for i, power in enumerate(power_output):
        print(f"  Stunde {i}: {power:.2f} kW")
    print("-" * 40)