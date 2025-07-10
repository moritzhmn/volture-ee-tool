from .base_generator import BaseGenerator
import pandas as pd
from .turbine_power_interpolation import get_turbine_power_value #Methode zum Abruf von cp basierend auf Klasse + Windgeschwindigkeit


#Wind Modell Klasse definieren mit Eigenschaften aus Base Generator und Zusätzlichen wie z.B. cut_in, WindModel erbt alle Methoden und Eigenschaften von BaseGenerator
class WindModel(BaseGenerator):
    def __init__(
        self,
        name,
        case,
        rated_power,
        location,
        hub_height =None,
        turbine_rated_power = None
    ):
        #Übergibt alle notwenidgen Paramter an die Basisklasse
        super().__init__(name, location, rated_power, case)

        #Definiert Standardwerte falls nicht vorhanden 
        self.hub_height = hub_height if hub_height is not None else 100
        self.turbine_rated_power = turbine_rated_power if turbine_rated_power is not None else 3.2
 
    #Ermittelt Hellmann-Konstante anhand des Szenaros Refernez: Volker Quaschning - Regenerative Energiesysteme
    @staticmethod
    def get_alpha(case):
        if case == 'best':
            alpha = 0.2066
        elif case == 'normal':
            alpha = 0.1737 #Stark raues Gelände (Wald, Stadt) 
        elif case == 'worst':
            alpha = 0.14366 #Mäßig raues Gelände (Felder, Dörfer)

        else:
            raise ValueError(f"Alpha für Sezenario: '{case}' nicht definiert!")
        return(alpha)
    
    #Ermittelt wake_loss Faktor anhand https://deutsche-windindustrie.de/wiki/parkeffekt-windenergieanlagen/#
    @staticmethod
    def get_wake_loss(case):
        if case == 'best':
            return 0.03   # 3 % Verlust bei idealem Layout
        elif case == 'normal':
            return 0.07  # 7 % mean Wert 
        elif case == 'worst':
            return 0.10  # 10 % max Wert
        else:
            raise ValueError(f"Wake Loss Faktor für Szenario: '{case}' nicht definiert!")
    
    #Ermittelt Sytsemwirkungsgrad (System: Trafo, Umrichter, Kabel etc.) Refernez: Volker Quaschning - Regenerative Energiesysteme
    @staticmethod
    def get_eta_sys(case):
        if case == 'best':
         eta_sys = 0.97
        elif case == 'normal':
         eta_sys = 0.95
        elif case == 'worst':
         eta_sys = 0.88
        else:
            raise ValueError(f"Kein Eintrag gefunden für Case '{case}'")
        return eta_sys

    #Hauptmethode zur Methode-Leistungssimulation   
    def simulate_power(self, weather_row):
        # Definiert Windgeschwindgkeit am Referenztag auf 10m Höhe 
        wind_speed_10 = weather_row.get("wind", None)
        if wind_speed_10 is None:
            raise ValueError("Windgeschwindigkeit nicht im Wetterdatensatz gefunden")
        # Extrahiere Zeit aus Wetterdaten
        timestamp = pd.to_datetime(weather_row["datetime"])
        # Warnung bei Windgeschwindigkeit = 0 zwischen 10–15 Uhr
        if 10 <= timestamp.hour <= 15 and wind_speed_10 == 0:
            print(f"Warnung: Windgeschwindigkeit ist 0 bei {timestamp} – mögliche fehlende oder fehlerhafte Wetterdaten.")

        # Windgeschwindikeit auf Nabenhöhe interpolieren
        wind_speed_hub = wind_speed_10 * (self.hub_height / 10) ** self.get_alpha(self.case)



        # Turbinenanzahl bestimmen
        turbine_count = max(1, round(self.rated_power / self.turbine_rated_power)) 
        # Turbinenleistung bestimmen 
        turbine_power_cal = get_turbine_power_value(self.turbine_rated_power, wind_speed_hub, self.case)
        # Parkleistung mit Parkverlusten und Systemverlusten berechnen
        park_power_cal = turbine_power_cal * turbine_count * (1 - self.get_wake_loss(self.case)) * self.get_eta_sys(self.case) / 1e6


        return park_power_cal