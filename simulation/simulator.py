from geopy.geocoders import Nominatim
from models.pv_model import PVModel
from models.wind_model import WindModel
from utils.data_loader import load_weather_data
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import calendar
from multiprocessing import Pool, cpu_count
from tqdm import tqdm




def resolve_locations(anlagen):
    geolocator = Nominatim(user_agent="volture", timeout=5)
    standort_coords = {}
    for anlage in anlagen:
        location = anlage.get("standort")
        if not location or location in standort_coords:
            continue
        try:
            loc = geolocator.geocode(location)
            if loc:
                standort_coords[location] = {
                    "latitude": float(loc.latitude),
                    "longitude": float(loc.longitude)
                }
            else:
                print(f"⚠️ Standort '{location}' konnte nicht aufgelöst werden.")
        except Exception as e:
            print(f"❌ Fehler beim Auflösen von '{location}': {e}")
    return standort_coords


def simulate_day(args):
    ref_date, anlage, case, season, coords, year_input = args

    name = anlage["name"]
    power = anlage["leistung_mw"]
    typ = anlage["typ"]
    location = anlage["standort"]
    latlon = coords.get(location)

    if not latlon:
     raise ValueError(f"❌ Keine Koordinaten für Standort '{location}' (Anlage: {name}). Simulation abgebrochen.")

    # ✅ Koordinaten-Tuple erzeugen
    coords_tuple = (latlon["latitude"], latlon["longitude"])

    ref_date_str = ref_date.strftime('%Y-%m-%d')
    weather = load_weather_data(location, ref_date_str, typ)

    # ✅ Modell initialisieren mit (lat, lon)-Tuple
    if typ == 'pv':
        model = PVModel(name=name, rated_power=power, location=coords_tuple, case=case)
    elif typ == 'wind':
        model = WindModel(name=name, rated_power=power, location=coords_tuple, case=case)
    else:
        return name, []

    time_series = []
    for hour in weather:
        power_out = model.simulate_power(hour)
        timestamp = pd.to_datetime(hour["datetime"])
        time_series.append({"timestamp": timestamp, "power_mw": power_out})

    return name, time_series


def create_generators(config, season, case, year_input):
    generators = []
    #Erstellt Liste mit allen Tagen des Monats der simuliert werden soll, year --> genriertes Jahr, year_input --> in main() festgelegtes Jahr
    year, month = year_input, season
    start_date = datetime.date(year, month, 1)
    end_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, end_day)
    date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    #Erstellt Standorte für alle Standorte der Anlagen die in Config gelistet sind
    anlagen = config.get("anlagen", [])
    standort_coords = resolve_locations(anlagen)

    #Taskliste die später mit Ausgaben gefüllt wird
    tasks = []

    #Prüft ob alle Anlagen einen gültigen Standort zugeteilt bekommen haben --> ansonsten Warnung
    for anlage in anlagen:
        if not anlage.get("standort") or anlage["standort"] not in standort_coords:
            print(f"⚠️ Anlage '{anlage['name']}' übersprungen (kein gültiger Standort).")
            continue
        for ref_date in date_range:
            #Erstellt die zu simulierenden Tage
            tasks.append((ref_date, anlage, case, season, standort_coords,year_input))

    print(f"🔧 Starte Multiprocessing mit {cpu_count()} Kernen für {len(tasks)} Aufgaben...")
    #Pool ist Klasse aus Multiprocessing Modul , pool ist selbstgewählt Instanz der Klasse
    with Pool(cpu_count()) as pool:
        #Erstellt leere Ergbnisliste
        results = []
        #Ermöglicht Fortschrittsanzeige
        pbar = tqdm(total=len(tasks), desc="🔄 Simuliere Tage", leave=False)
        #Übergibt alle Tasks an simulate_day Funktion --> zeitgleiche Ausführung zu Performance-Steigerung
        for result in pool.imap_unordered(simulate_day, tasks):
            results.append(result)
            pbar.update()
        pbar.close()

    #Leere generator_map (Dictionary) wird erstellt
    generator_map = {}
    #Gruppiert alle Zeitreihen pro Anlage
    for name, times in results:
        if name not in generator_map:
            generator_map[name] = []
        generator_map[name].extend(times)

    for name, times in generator_map.items():
        typ = next((a["typ"] for a in anlagen if a["name"] == name), "unknown")
        location = next((a["standort"] for a in anlagen if a["name"] == name), "unknown")
        generators.append({
            "name": name,
            "typ": typ,
            "location": location,
            "time_series": times
        })

    # 📊 Tagesenergie aggregieren & typische Tage visualisieren
    all_series = []

    #Zeitreihen in DataFrames umwandeln (Tabelle aus timestamp und power)
    for gen in generators:
        name = gen["name"]  # z. B. "Windpark_Nord"
        ts = pd.DataFrame(gen["time_series"])
        ts['timestamp'] = pd.to_datetime(ts['timestamp'])
        ts = ts.sort_values('timestamp')
        ts = ts.set_index('timestamp')
        ts = ts.rename(columns={"power_mw": name})  # Spalte eindeutig benennen
        all_series.append(ts)

    # Zeitreihen aller Anlagen zusammenführen
    total_df = pd.concat(all_series, axis=1).fillna(0)
    #Summierung der Leistung 
    # Summierte Leistung als neue Spalte hinzufügen
    total_df['power_sum'] = total_df.sum(axis=1)
 

    # Rückgabe der typischen Tagesprofile als DataFrames
    return total_df.reset_index()