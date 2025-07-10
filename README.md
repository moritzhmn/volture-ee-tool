# Volture-EE-Tool

Dieses Projekt simuliert die Energieerzeugung von Photovoltaik- und Windkraftanlagen an verschiedenen Standorten in Deutschland basierend auf Wetterdaten des DWD.

---

## 1. Installation der Abhängigkeiten

### 1.1 Repository klonen

```bash
git clone https://github.com/dein-benutzername/dein-repo.git
cd dein-repo
```

### 1.2 Virtuelle Umgebung erstellen und aktivieren

### Windows:
```bash
py -m venv venv
venv\Scripts\activate
```

### Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Bibliotheken installieren

```bash
pip install -r requirements.txt
```
##### Alternativ globale Installation (nicht empfohlen):

```bash
pip install pvlib pandas numpy geopy matplotlib tqdm requests pyyaml joblib
```
---

## 2. Konfiguration der Anlagen

Lege eine Datei config/anlagen.yaml mit folgendem Aufbau an:

```bash
anlagen:
  - name: PV_Berlin
    typ: wind
    leistung_mw: 20
    standort: Potsdam
  - name: Wind_Nuernberg
    typ: wind
    leistung_mw: 15
    standort: Nuernberg
```

#### Hinweise:
- Der Standort muss exakt einer Station aus der Liste entsprechen (siehe Verfügbare Stationen).
- Die Station kann mithilfe der Datei config/wetterstationen_interaktiv.html im Browser gefunden werden.

---

## 3. Simulation starten

In main.py kann der Simulationszeitraum eingestellt werden:

```bash
season = 5  # für Mai
year = 2025  # Jahr
```
Optional kann in simulator.py ein bestimmter Tag simuliert werden:

Beispiel für 12. Mai 2025:
```bash
date_range = [datetime.date(2025, 5, 12)]
```

Wichtig: Monat und Jahr in main.py müssen mit dem Tagesdatum übereinstimmen!

---

## 4. Anpassen von Modellparametern

Standardparameter können in den Modellen wie folgt geändert werden:

```bash
self.hub_height = hub_height if hub_height is not None else 100
self.turbine_rated_power = turbine_rated_power if turbine_rated_power is not None else 3.2
```
---

## 5. Auswahl des DWD-Endpunkts

Je nach Simulationszeitraum muss der Datenendpunkt angepasst werden:

Aktuelle Daten (letzte ca. 2 Jahre):
```bash
url = f"https://opendata.dwd.de/.../recent/10minutenwerte_{code}_{station_id}_akt.zip"
```

Historische Daten:
```bash
url = f"https://opendata.dwd.de/.../historical/10minutenwerte_{code}_{station_id}_{start_str}_{end_string}_hist.zip"
```

Verfügbare Datenquellen:
- Solar: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/solar/
- Wind: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/wind/

---

## 6. Simulation ausführen

Cache ggf. leeren.

Starte die Simulation mit:
```bash
python main.py
```
Beobachte die Konsolenausgabe zur Fehlersuche. Es kann vorkommen, dass für einige Zeiträume keine Wetterdaten verfügbar sind.

---

## 7. Ergebnisse abrufen

Die Ergebnisse findest du im output/ Ordner.

---

## Verfügbare Stationen (Auszug)

Aachen-Orsbach, Ahaus, Alfeld, Angermuende, Arkona, Augsburg, Bamberg, Belm, Berlin Brandenburg, Berlin-Tegel, Berus, Boizenburg, Braunschweig, Bremen, Bremerhaven, Chemnitz, Cottbus, Cuxhaven, Duesseldorf, Emden, Freiburg, Garmisch-Partenkirchen, Hamburg-Fuhlsbuettel, Hannover, Leipzig/Halle, Mannheim, Muenster/Osnabrueck, Nuernberg, Potsdam, Regensburg, Rostock-Warnemuende, Saarbruecken-Ensheim, Stuttgart, Trier-Petrisberg, Weimar, Wuerzburg, Zugspitze, uvm.

Zur Bestimmung der nächstgelegenen Wetterstation siehe config/wetterstationen_interaktiv.html.
