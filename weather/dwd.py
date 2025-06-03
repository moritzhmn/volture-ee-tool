import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min

# === 0. Definiere Pfade für die Jahreszeiten ===
seasons = {
    "Sommer_August": {
        "pv": "/Users/moritzhomann/Downloads/energy-charts_Globale_Solarstrahlung_in_Deutschland_im_August_2024.csv",
        "wind": "/Users/moritzhomann/Downloads/energy-charts_Windgeschwindigkeit_in_Deutschland_im_August_2024.csv"
    },
    "Winter_Januar": {
        "pv": "/Users/moritzhomann/Downloads/energy-charts_Globale_Solarstrahlung_in_Deutschland_im_Januar_2024.csv",
        "wind": "/Users/moritzhomann/Downloads/energy-charts_Windgeschwindigkeit_in_Deutschland_im_Januar_2024.csv"
    },
    "Fruehling_April": {
        "pv": "/Users/moritzhomann/Downloads/energy-charts_Globale_Solarstrahlung_in_Deutschland_im_April_2024.csv",
        "wind": "/Users/moritzhomann/Downloads/energy-charts_Windgeschwindigkeit_in_Deutschland_im_April_2024.csv"
    },
    "Herbst_Oktober": {
        "pv": "/Users/moritzhomann/Downloads/energy-charts_Globale_Solarstrahlung_in_Deutschland_im_Oktober_2024.csv",
        "wind": "/Users/moritzhomann/Downloads/energy-charts_Windgeschwindigkeit_in_Deutschland_im_Oktober_2024.csv"
    }
}

locations = ["Bremen", "Dresden", "Giessen", "Saarbruecken", "Wuerzburg"]

def load_and_process_season(pv_path, wind_path):
    print(f"Lade PV-Daten von: {pv_path}")
    df_pv = pd.read_csv(pv_path, skiprows=[1], index_col=0, parse_dates=True)
    df_pv.columns = locations
    df_pv = df_pv.sort_index()
    print(f"PV-Daten geladen: {df_pv.shape} Zeilen x Spalten")
    print(f"PV Index dtype: {df_pv.index.dtype}, tz: {getattr(df_pv.index, 'tz', None)}")

    print(f"Lade Wind-Daten von: {wind_path}")
    df_wind = pd.read_csv(wind_path, skiprows=[1], index_col=0, parse_dates=True)
    df_wind.columns = locations
    df_wind = df_wind.sort_index()
    print(f"Wind-Daten geladen: {df_wind.shape} Zeilen x Spalten")
    print(f"Wind Index dtype: {df_wind.index.dtype}, tz: {getattr(df_wind.index, 'tz', None)}")

    # Kombinierte Daten zusammenführen
    df_combined = pd.concat([
        df_pv.add_suffix("_PV"),
        df_wind.add_suffix("_Wind")
    ], axis=1)
    print(f"Kombinierte Daten Form: {df_combined.shape}")
    print(f"Kombinierter Index dtype vor TZ-Check: {df_combined.index.dtype}, tz: {getattr(df_combined.index, 'tz', None)}")

    # Wenn Index tz-aware ist, erst Zeitzone entfernen
    def has_mixed_tz(index):
        tz_aware = [isinstance(x, pd.Timestamp) and x.tzinfo is not None for x in index]
        return any(tz_aware) and not all(tz_aware)

    def has_any_tz(index):
        return any(isinstance(x, pd.Timestamp) and x.tzinfo is not None for x in index)

    if isinstance(df_combined.index, pd.DatetimeIndex):
        if df_combined.index.tz is not None:
            print(f"Entferne Zeitzone {df_combined.index.tz} vom Index.")
            df_combined.index = df_combined.index.tz_localize(None)
    else:
        # Index ist kein DatetimeIndex
        if has_mixed_tz(df_combined.index):
            print("Index enthält gemischte tz-aware und tz-naive Werte, konvertiere mit utc=True")
            df_combined.index = pd.to_datetime(df_combined.index, utc=True)
            # Optional zurück konvertieren in MESZ, dann tz entfernen
            df_combined.index = df_combined.index.tz_convert('Europe/Berlin').tz_localize(None)
        elif has_any_tz(df_combined.index):
            # Alle tz-aware, aber noch kein DatetimeIndex, dann ebenfalls utc=True
            print("Index enthält ausschließlich tz-aware Werte, konvertiere mit utc=True")
            df_combined.index = pd.to_datetime(df_combined.index, utc=True)
            df_combined.index = df_combined.index.tz_convert('Europe/Berlin').tz_localize(None)
        else:
            print("Index enthält nur tz-naive Werte, konvertiere normal mit pd.to_datetime()")
            df_combined.index = pd.to_datetime(df_combined.index)

    # Debug: Ausgabe der ersten Indexeinträge
    print("Erste Indexeinträge:")
    print(df_combined.index[:5])

    # Prüffunktion für gültige Tage
    def is_full_day(group, day):
        valid = (len(group) == 24) and (not group.isna().any().any())
        if not valid:
            print(f"Ungültiger Tag gefunden: {day} mit {len(group)} Einträgen und NaNs: {group.isna().any().any()}")
        return valid

    # Gruppenbildung nach Tagen
    daily_groups = df_combined.groupby(df_combined.index.date)

    # Gültige Tage herausfiltern
    valid_days = [day for day, group in daily_groups if is_full_day(group, day)]
    print(f"Anzahl gültiger Tage: {len(valid_days)}")

    # Nur Daten für gültige Tage behalten
    df_valid = df_combined[pd.Index(df_combined.index.date).isin(valid_days)]
    print(f"Form df_valid: {df_valid.shape}")

    return df_valid, valid_days

def cluster_and_find_typicals(df_valid):
    print("Starte Clustering...")
    daily_profiles = df_valid.groupby(df_valid.index.date).apply(lambda x: x.values.flatten())
    X = np.vstack(daily_profiles.values)
    print(f"Cluster-Input-Datenform: {X.shape}")

    kmeans = KMeans(n_clusters=5, random_state=42)
    labels = kmeans.fit_predict(X)
    medoid_indices, _ = pairwise_distances_argmin_min(kmeans.cluster_centers_, X)
    typical_days = pd.to_datetime(daily_profiles.index[medoid_indices])
    print(f"Typische Tage gefunden: {typical_days}")

    return typical_days

def best_worst_normal_cases(df_valid, valid_days):
    print("Bestimme Best-, Worst- und Normalfälle...")

    daily_pv_sum = df_valid.filter(like="_PV").groupby(df_valid.index.date).sum().sum(axis=1)
    daily_wind_sum = df_valid.filter(like="_Wind").groupby(df_valid.index.date).sum().sum(axis=1)

    daily_pv_sum = daily_pv_sum[daily_pv_sum.index.isin(valid_days)]
    daily_wind_sum = daily_wind_sum[daily_wind_sum.index.isin(valid_days)]

    print(f"PV Summen Tageswerte Beispiel:\n{daily_pv_sum.head()}")
    print(f"Wind Summen Tageswerte Beispiel:\n{daily_wind_sum.head()}")

    best_case_day = daily_pv_sum.idxmax() if len(daily_pv_sum) > 0 else None
    worst_case_day = daily_pv_sum.idxmin() if len(daily_pv_sum) > 0 else None
    best_wind_day = daily_wind_sum.idxmax() if len(daily_wind_sum) > 0 else None
    worst_wind_day = daily_wind_sum.idxmin() if len(daily_wind_sum) > 0 else None

    best_case_candidates = set([best_case_day, best_wind_day])
    worst_case_candidates = set([worst_case_day, worst_wind_day])

    def get_combined_case(candidates):
        for day in candidates:
            if day in valid_days:
                return day
        return None

    best_case = get_combined_case(best_case_candidates)
    worst_case = get_combined_case(worst_case_candidates)

    normal_case = None
    try:
        typical_days = cluster_and_find_typicals(df_valid)
        normal_case = typical_days[0].date()
    except Exception as e:
        print(f"Fehler beim Clustern: {e}")

    print(f"Best Case: {best_case}, Worst Case: {worst_case}, Normal Case: {normal_case}")

    return best_case, worst_case, normal_case

def best_worst_normal_cases_per_location(df_valid, valid_days):
    results = {}
    for loc in locations:
        pv_col = loc + "_PV"
        wind_col = loc + "_Wind"

        daily_pv_sum = df_valid[[pv_col]].groupby(df_valid.index.date).sum()[pv_col]
        daily_wind_sum = df_valid[[wind_col]].groupby(df_valid.index.date).sum()[wind_col]

        daily_pv_sum = daily_pv_sum[daily_pv_sum.index.isin(valid_days)]
        daily_wind_sum = daily_wind_sum[daily_wind_sum.index.isin(valid_days)]

        best_case_day = daily_pv_sum.idxmax() if len(daily_pv_sum) > 0 else None
        worst_case_day = daily_pv_sum.idxmin() if len(daily_pv_sum) > 0 else None
        best_wind_day = daily_wind_sum.idxmax() if len(daily_wind_sum) > 0 else None
        worst_wind_day = daily_wind_sum.idxmin() if len(daily_wind_sum) > 0 else None

        best_case_candidates = set([best_case_day, best_wind_day])
        worst_case_candidates = set([worst_case_day, worst_wind_day])

        def get_combined_case(candidates):
            for day in candidates:
                if day in valid_days:
                    return day
            return None

        best_case = get_combined_case(best_case_candidates)
        worst_case = get_combined_case(worst_case_candidates)

        results[loc] = {
            "best_case": best_case,
            "worst_case": worst_case,
        }

        print(f"{loc}: Best Case = {best_case}, Worst Case = {worst_case}")

    return results

# === Hauptlogik für alle Jahreszeiten ===
all_results = []

for season_name, paths in seasons.items():
    print(f"\nVerarbeite Saison: {season_name}")

    df_valid, valid_days = load_and_process_season(paths["pv"], paths["wind"])

    # Deutschland (aggregiert)
    best_case, worst_case, normal_case = best_worst_normal_cases(df_valid, valid_days)

    # Regionen einzeln
    region_results = best_worst_normal_cases_per_location(df_valid, valid_days)

    # Ergebnisse sammeln
    all_results.append({
        "Saison": season_name,
        "Standort": "Deutschland",
        "Best Case": best_case,
        "Worst Case": worst_case,
        "Normal Case": normal_case
    })

    for loc, vals in region_results.items():
        all_results.append({
            "Saison": season_name,
            "Standort": loc,
            "Best Case": vals["best_case"],
            "Worst Case": vals["worst_case"],
            "Normal Case": None  # Für einzelne Standorte kein Cluster Normal Case definiert (kann erweitert werden)
        })

# === Ergebnisse als CSV speichern ===
df_results = pd.DataFrame(all_results)
df_results.to_csv("typische_erzeugungstage_jahreszeiten.csv", index=False)
print("\nCSV-Datei 'typische_erzeugungstage_jahreszeiten.csv' wurde gespeichert.")