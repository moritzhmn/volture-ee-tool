import pandas as pd
import numpy as np

#CSV einlesen und vorbereiten 
df = pd.read_csv("config/power_curves.csv", sep=",")

#Turbinentyp und Nennleistung extrahieren
df[['turbine_model', 'rated_power_kw']] = df['turbine_type'].str.extract(r'(.+)/(\d+)', expand=True)
df['rated_power_kw'] = df['rated_power_kw'].astype(float)

#Relevante Windgeschwindigkeits-Spalten erkennen
excluded = {'turbine_type', 'turbine_model', 'rated_power_kw'}
wind_cols = [col for col in df.columns if col not in excluded and col.replace('.', '', 1).isdigit()]
df[wind_cols] = df[wind_cols].apply(pd.to_numeric, errors='coerce')

#Klasseneinteilung nach Nennleistung (in kW)
bins = [0, 1000, 2000, 2300, 2600, 3000, 3300, 3700, 5200, np.inf]
labels = ['<1 MW', '1-2 MW', '2.0–2.3 MW', '2.3–2.6 MW', '2.6–3.0 MW',
          '3.0–3.3 MW', '3.3–3.7 MW', '3.7–5.2 MW', '>=5.2 MW']
df['class'] = pd.cut(df['rated_power_kw'], bins=bins, labels=labels)

#Windgeschwindigkeiten als float-Liste (für Interpolation)
wind_speeds = np.array(sorted([float(c) for c in wind_cols]))

#Interpolation einer Einzelkurve mit gültigen Punkten ===
def interpolate_curve(row):
    raw = row[wind_cols].astype(float)
    wind = np.array([float(w) for w in wind_cols])
    return np.interp(wind_speeds, wind[~raw.isna()], raw.dropna())

#Leistungswert für bestimmte Windgeschwindigkeit + Case ===
def get_turbine_power_value(target_mw, wind_speed, case):
    target_kw = target_mw * 1000
    class_idx = np.digitize([target_kw], bins)[0] - 1
    selected_class = labels[class_idx]
    class_df = df[df['class'] == selected_class]

    if class_df.empty:
        raise ValueError(f"Keine Turbinen in Klasse '{selected_class}' gefunden")

    #Interpolation
    curves = class_df[wind_cols].apply(interpolate_curve, axis=1, result_type='expand')
    curves = curves.dropna(how='all')  #löscht Kurven bei denen Interpolation nicht geht
    curves.columns = wind_speeds

    avg_curve = curves.mean(axis=0) #Spaltenweise Durchschnittsbildung für eine mean-Kurve 
    total_outputs = curves.sum(axis=1) #Zeilenweise Summenbildung 
    best_curve = curves.loc[total_outputs.idxmax()] 
    worst_curve = curves.loc[total_outputs.idxmin()]

    if case == 'best':
        selected_curve = best_curve.values
    elif case == 'worst':
        selected_curve = worst_curve.values
    elif case == 'normal':
        selected_curve = avg_curve.values
    else:
        raise ValueError(f"Unbekannter case '{case}'")
    return np.interp(wind_speed, wind_speeds, selected_curve)

