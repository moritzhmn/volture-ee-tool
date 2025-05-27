from .base_generator import BaseGenerator
import pvlib
import pandas as pd
import numpy as np

class PVModel(BaseGenerator):
    def __init__(
        self,
        name,
        rated_power,       # [kW] STC-Leistung
        age,               # [Jahre]
        shading,           # z. B. 0.1 = 10% Abschattung
        albedo,            # z. B. 0.2 für typische Umgebungen
        azimuth,            # Azimuth der PV-Fläche in Grad
        D_soil,            # Verschmutzungsgrad
        tilt,              # Neigung in Grad 
        size,              # Fläche der Anlage [m²]
        location=None,     # (Breite, Länge)
        degradation_rate=0.005,  # jährliche Degradation (z. B. 0.5%)
    ):
        super().__init__(name, location)
        self.rated_power = rated_power
        self.age = age
        self.shading = shading
        self.albedo = albedo
        self.azimuth = azimuth
        self.D_soil = D_soil
        self.tilt = tilt
        self.size = size
        self.location = location
        self.degradation_rate = degradation_rate


    def simulate_power(self, weather_row):
        # Wetterdaten
        GTI = weather_row["GTI"]  # [W/m²]
        timestamp = pd.Timestamp(weather_row["time"], tz='UTC')

        # Standortkoordinaten
        lat, lon = self.location

        # STC-Leistung in Watt
        P_STC = self.rated_power 

        # Verluste
        PR = 0.75
   
        # Momentanleistung berechnen
        P_t = P_STC * (GTI / 1000) * PR

        # Begrenzung auf STC
        P_t = min(P_t, P_STC)

        return P_t 