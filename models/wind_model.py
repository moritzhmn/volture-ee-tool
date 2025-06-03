from .base_generator import BaseGenerator
from .turbine_power_interpolation import get_turbine_power_value # Funktion zum Abruf von cp basierend auf Klasse + Windgeschwindigkeit

class WindModel(BaseGenerator):
    def __init__(
        self,
        name,
        case,
        rated_power,
        location,
        cut_in =None,
        cut_out =None,
        hub_height =None,
        turbine_rated_power = None
    ):
        super().__init__(name, location, rated_power, case)
        self.cut_in = cut_in if cut_in is not None else 3
        self.cut_out = cut_out if cut_out is not None else 25
        self.hub_height = hub_height if hub_height is not None else 100
        self.turbine_rated_power = turbine_rated_power if turbine_rated_power is not None else 3.2

    @staticmethod
    def get_alpha(case):
        if case == 'best':
            alpha = 0.14 #flaches offenes Land
        elif case == 'worst':
            alpha = 0.3 #Stark raues Gelände (Wald, Stadt) 
        elif case == 'normal':
            alpha = 0.2 #Mäßig raues Gelände (Felder, Dörfer)

        else:
            raise ValueError(f"Alpha für Sezenario: '{case}' nicht definiert!")
        return(alpha)
    
    @staticmethod
    def get_wake_loss(case):
        if case == 'best':
            return 0.03   # 3 % Verlust bei idealem Layout
        elif case == 'normal':
            return 0.10   # 10 % typischer Wake-Loss
        elif case == 'worst':
            return 0.15   # 15 % z. B. bei dichten Parks mit viel Turbulenz
        else:
            raise ValueError(f"Wake Loss Faktor für Szenario: '{case}' nicht definiert!")
    
    @staticmethod
    def get_eta_sys(case):
        if case == 'best':
         eta_sys = 0.95 
        elif case == 'worst':
         eta_sys = 0.82
        elif case == 'normal':
         eta_sys = 0.90
        else:
            raise ValueError(f"Kein Eintrag gefunden für Case '{case}'")
        return eta_sys

      
    def simulate_power(self, weather_row):
        #Definiert Windgeschwindgkeit am Referenztag auf 10m Höhe 
        wind_speed_10 = weather_row.get("wind", None)
        if wind_speed_10 is None:
            raise ValueError("Windgeschwindigkeit nicht im Wetterdatensatz gefunden")
        #Windgeschwindikeit auf Nabenhöhe interpolieren
        wind_speed_hub = wind_speed_10 * (self.hub_height/10) ** self.get_alpha(self.case)

        #Prüft ob Windgeschwindigkeit im Arbeitsbereich liegt
        if wind_speed_hub < self.cut_in or wind_speed_hub > self.cut_out:
         return 0
        #Turbinenanzahl bestimmen
        turbine_count = max(1,round(self.rated_power / self.turbine_rated_power)) 
        #Trubinenleistung bestimmen 
        turbine_power_cal = get_turbine_power_value(self.turbine_rated_power, wind_speed_hub, self.case)
        # Parkleistung mit Parkverlusten und Systemverlusten berechnen
        park_power_cal = turbine_power_cal * turbine_count * (1-self.get_wake_loss(self.case)) * self.get_eta_sys(self.case) /1e6


 
        return park_power_cal 