def main():
    import os
    from utils.data_loader_dwd import load_yaml_config
    from simulation.simulator import create_generators
    from tqdm import tqdm
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
 
    #Konfiguraions Pfade
    config_path = 'config/anlagen.yaml'
    output_base_path = "output/"
    
    #Lädt Konfiguration mithilfe der in data_loader definierten Methode load_yaml_config
    config = load_yaml_config(config_path)

    #Definiert zu Siumlierenden Monat
    season = 5
    year = 2025

    #Liste der im Zeitraum zu simulierenden Szenarieren --> Einfluss in PV und Wind Modell gewählten Parameter
    cases = ['best','worst','normal']

    #Schleife läuft Szenarien durch
    for case in tqdm(cases, desc="Verarbeite Szenarien"):
        #Ruft Simulationsprogramm create_generators auf
        df = create_generators(config, season, case, year)  # DataFrame mit allen Anlagen + power_sum

        # Sicherstellen, dass timestamp als datetime vorliegt
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        # Aggregationen pro Tag
        daily_max = df.groupby('date')['power_sum'].max()
        daily_min = df.groupby('date')['power_sum'].min()
        daily_ptp = daily_max - daily_min  # Peak-to-Peak Leistung

        # max 5 min Sprungänderung berechnen (per Tag)
        daily_diff = df.groupby('date')['power_sum'].apply(lambda x: x.diff().abs().max())

        # Tage mit den gewünschten Eigenschaften
        max_day = daily_max.idxmax()
        min_day = daily_min.idxmin()
        volatile_day = daily_ptp.idxmax()
        sharp_change_day = daily_diff.idxmax()

        # Tagesprofile extrahieren
        max_day_df = df[df['date'] == max_day]
        min_day_df = df[df['date'] == min_day]
        volatile_day_df = df[df['date'] == volatile_day]
        sharp_change_day_df = df[df['date'] == sharp_change_day]

        # Ordner mit season (zweistellig) und year als Name anlegen
        folder_name = f"{season:02d}_{year}"
        output_path = os.path.join(output_base_path, folder_name)
        os.makedirs(output_path, exist_ok=True)

        # Basis-Dateiname
        base_filename = f"time_series_{case}_{season:02d}_{year}"

        # Gesamte Zeitreihe speichern
        df.to_csv(os.path.join(output_path, base_filename + ".csv"), index=False)

        # Typische Tage speichern
        max_day_df.to_csv(os.path.join(output_path, f"{base_filename}_max_day.csv"), index=False)
        min_day_df.to_csv(os.path.join(output_path, f"{base_filename}_min_day.csv"), index=False)
        volatile_day_df.to_csv(os.path.join(output_path, f"{base_filename}_volatile_day.csv"), index=False)
        sharp_change_day_df.to_csv(os.path.join(output_path, f"{base_filename}_sharp_change_day.csv"), index=False)

        # --- Plots der Referenztage ---
        plt.figure(figsize=(12, 8))
        plt.plot(max_day_df['timestamp'], max_day_df['power_sum'], label=f"Max Leistung Tag: {max_day}")
        plt.plot(min_day_df['timestamp'], min_day_df['power_sum'], label=f"Min Leistung Tag: {min_day}")
        plt.plot(volatile_day_df['timestamp'], volatile_day_df['power_sum'], label=f"Volatile Tag: {volatile_day}")
        plt.plot(sharp_change_day_df['timestamp'], sharp_change_day_df['power_sum'], label=f"Sharp Change Tag: {sharp_change_day}")

        # --- Einstellungen des Plots ---  
        plt.xlabel("Timestamp")
        plt.ylabel("Leistung (MW)")
        plt.title(f"Referenz-Tagesprofile für Szenario '{case}' - {season:02d}/{year}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # Wasserzeichen hinzufügen (halbtransparent, diagonal)
        plt.figtext(0.5, 0.5, "MH_EE", fontsize=40, color='gray', alpha=0.2, ha='center', va='center', rotation=30)

        # Plot speichern
        plt.savefig(os.path.join(output_path, f"{base_filename}_referenz_tage_plot.png"))
        plt.close()

if __name__ == "__main__":
    main()