import sys
from utils.data_loader import load_yaml_config
from simulation.simulator import create_generators, run_simulation

def main():
    if len(sys.argv) != 3:
        print("Benutzung: python main.py <config.yaml> <output.csv>")
        sys.exit(1)

    config_path = sys.argv[1]
    output_csv = sys.argv[2]

    config = load_yaml_config(config_path)
    generators = create_generators(config)
    results = run_simulation(generators)

    # Beispiel CSV speichern
    import pandas as pd
    df_list = []
    for model_name, power_output in results.items():
        df = pd.DataFrame(power_output)
        df["model"] = model_name
        df_list.append(df)
    all_results = pd.concat(df_list)
    all_results.to_csv(output_csv, index=False)

    print("Simulation abgeschlossen. Ergebnisse gespeichert in:", output_csv)

if __name__ == "__main__":
    main()