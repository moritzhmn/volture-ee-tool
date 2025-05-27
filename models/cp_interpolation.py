import pandas as pd
import numpy as np

# === CSV einlesen und vorbereiten ===
df = pd.read_csv("/Users/moritzhomann/volture-ee-tool/power_curves.csv", sep=",")

df[['turbine_model', 'rated_power_mw']] = df['turbine_type'].str.extract(r'(.+)/(\d+)', expand=True)
df['rated_power_mw'] = df['rated_power_mw'].astype(float)

excluded = {'turbine_type', 'turbine_model', 'rated_power_mw'}
wind_cols = [col for col in df.columns if col not in excluded and col.replace('.', '', 1).isdigit()]

df[wind_cols] = df[wind_cols].apply(pd.to_numeric, errors='coerce')

bins = [0, 1000, 2000, 2300, 2600, 3000,3300, 3700, 5200, np.inf]
labels = ['<1 MW', '1-2 MW', '2.0–2.3 MW', '2.3–2.6 MW', '2.6–3.0 MW', '3.0–3.3 MW','3.3–3.7 MW', '3.7–5.2 MW', '>=5.2 MW']
df['class'] = pd.cut(df['rated_power_mw'], bins=bins, labels=labels)

# Mittelwerte je Klasse mit Interpolation
class_avg_curves = {}
for label in labels:
    class_df = df[df['class'] == label]
    if class_df.empty:
        continue
    class_df_interp = class_df[wind_cols].apply(lambda row: row.interpolate(limit_direction="both"), axis=1)
    mean_curve = class_df_interp.mean()
    class_avg_curves[label] = mean_curve

# Windgeschwindigkeiten als float (Index für Interpolation)
wind_speeds = np.array(sorted([float(c) for c in wind_cols]))

def get_turbine_power(turbine_class, wind_speed):
    """
    Liefert interpolierten Leistungswert für Turbinenklasse und Windgeschwindigkeit.
    """
    print(turbine_class)
    if turbine_class not in class_avg_curves:
        raise ValueError(f"Turbinenklasse '{turbine_class}' nicht gefunden")

    curve = class_avg_curves[turbine_class]
    curve_ws = curve.index.astype(float).values
    curve_vals = curve.values

    # Bereich prüfen (außerhalb 0)
    if wind_speed < curve_ws.min() or wind_speed > curve_ws.max():
        return 0.0

    return np.interp(wind_speed, curve_ws, curve_vals)

