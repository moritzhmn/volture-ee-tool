import time
from utils.data_loader import load_yaml_config
from simulation.simulator import create_generators, run_simulation

start_total = time.time()
print("[INFO] Lade Konfiguration ...")
config = load_yaml_config("config.yaml")

print("[INFO] Erstelle Generatoren ...")
start_gen = time.time()
generators = create_generators(config)
print(f"[INFO] Generatoren erstellt in {time.time() - start_gen:.2f}s")

print("[INFO] Starte Simulation ...")
start_sim = time.time()
results = run_simulation(generators)
print(f"[INFO] Simulation abgeschlossen in {time.time() - start_sim:.2f}s")

print(f"[INFO] Gesamtlaufzeit: {time.time() - start_total:.2f}s")
print("-" * 40)

# Strukturierte Ausgabe der Ergebnisse
for model_name, power_output in results.items():
    print(f"Ergebnisse für {model_name}:")
    for i, power in enumerate(power_output):
        print(f"  Stunde {i}: {power:.2f} MW")
    print("-" * 40)