import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Parameter: automatische Zeitverschiebung aktivieren? ===
use_shift = False # << auf True setzen, um automatische Verschiebung zu aktivieren

# === Datei 1: PV-Simulation ===
df_pv = pd.read_csv("/Users/moritzhomann/Dokumente Lokal/volture-ee-tool/output/06_2025/time_series_best_06_2025.csv")
df_pv["timestamp"] = pd.to_datetime(df_pv["timestamp"])
df_pv["timestamp"] += pd.Timedelta(hours=2)  # UTC → lokale Zeit
df_pv = df_pv.set_index("timestamp")
df_pv = df_pv.round(6)
df_pv.index = df_pv.index.round("1min")

# === Datei 2: Validierung (Messung) ===
df_val = pd.read_csv("/Users/moritzhomann/Dokumente Lokal/volture-ee-tool/validation data pv/Potsdam 0.0324 MW.csv", sep=";", header=None, names=["timestamp", "value"])
df_val["timestamp"] = pd.to_datetime(df_val["timestamp"], format="%Y/%m/%d %H:%M:%S")
df_val = df_val.set_index("timestamp")
df_val.index = df_val.index.round("1min")

# === Filtern auf spezifisches Datum ===
df_pv = df_pv.loc["2025-06-12"]
df_val = df_val.loc["2025-06-12"]

# === Zeitverschiebung vorbereiten ===
best_lag = 0
best_corr = None

if use_shift:
    print("⏱ Automatische Zeitverschiebung aktiv …")
    best_corr = -np.inf
    max_lag = 60  # teste Verschiebungen von -60 bis +60 Minuten

    for lag in range(-max_lag, max_lag + 1):
        shifted = df_pv["PV_Berlin"].shift(periods=lag, freq='min')
        temp = pd.DataFrame({"sim": shifted, "val": df_val["value"]}).dropna()
        if len(temp) > 2:
            corr = temp["sim"].corr(temp["val"])
            if corr > best_corr:
                best_corr = corr
                best_lag = lag
    print(f"Beste Zeitverschiebung: {best_lag} Minuten (Korrelation: {best_corr:.3f})")
else:
    print("🕑 Nur manuelle Zeitverschiebung (UTC+2), kein automatisches Shifting.")
    best_lag = 0  # keine zusätzliche Verschiebung
    common = df_pv[["PV_Berlin"]].join(df_val[["value"]], how="inner")
    if len(common) > 2:
        best_corr = common["PV_Berlin"].corr(common["value"])

# === Zeitverschiebung anwenden (immer gleich) ===
df_pv_shifted = df_pv.copy()
df_pv_shifted.index = df_pv_shifted.index + pd.Timedelta(minutes=best_lag)

# === Gemeinsame Zeitpunkte nach Verschiebung ===
df_pv_sorted = df_pv_shifted.reset_index().sort_values("timestamp")  # ✅ Jetzt korrekt
df_val_sorted = df_val.reset_index().sort_values("timestamp")

merged = pd.merge_asof(df_pv_sorted, df_val_sorted,
                       on="timestamp",
                       direction="nearest",
                       tolerance=pd.Timedelta("1min"))  # Toleranz 1 Minute

merged = merged.dropna(subset=["value"])  # Nur Paare mit Messwert behalten

print(f"Anzahl Datenpaare nach merge_asof: {len(merged)}")

if len(merged) > 2:
    best_corr = merged["PV_Berlin"].corr(merged["value"])
    print(f"Korrelation nach merge_asof: {best_corr:.3f}")
else:
    best_corr = None
    print("Nicht genügend gemeinsame Datenpunkte für Korrelation.")




# === Plot ===
plt.figure(figsize=(12, 5))
plt.plot(df_pv_shifted.index, df_pv_shifted["PV_Berlin"], label="Simulation (verschoben)" if use_shift else "Simulation", color="blue")
plt.plot(df_val.index, df_val["value"], label="Messwert", color="orange", linestyle="dashed")

plt.xlabel("Zeit")
plt.ylabel("Leistung / Wert")
corr_str = f"{best_corr:.2f}" if best_corr is not None else "n/a"
plt.title(f"Simulation vs. Messwert am 2025-06-12\n{'Optimale Verschiebung' if use_shift else 'Nur UTC-Korrektur'}: {best_lag} min – Korrelation: {corr_str}")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.xticks(rotation=45)
plt.savefig("validation data pv/plots/berlin_wetter_aber_postdam_0.0324_12_06_2025_best.pdf", format="pdf", dpi=600)
plt.show()