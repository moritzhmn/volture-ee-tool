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
        azimut,            # Azimut der PV-Fläche in Grad
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
        self.azimut = azimut
        self.D_soil = D_soil
        self.tilt = tilt
        self.size = size
        self.location = location
        self.degradation_rate = degradation_rate

    def simulate_power(self, weather_row):
        # GHI aus Wetterdaten (in W/m²)
        GHI = weather_row["GHI"]
        #Temperatur aus Wetterdaten (wenn nicht vorhanen standardmäßig auf 0 gesetzt)
        T_air = weather_row.get("temperature", 25)
        timestamp = pd.Timestamp(weather_row["time"], tz='UTC')

        # Standort und Sonnenstand
        lat, lon = self.location
        site = pvlib.location.Location(lat, lon)
        solar_pos = site.get_solarposition(timestamp)
        zenith = solar_pos["zenith"].iloc[0]
        azimuth_sun = solar_pos["azimuth"].iloc[0]

        # Einstrahlwinkel (AOI)
        theta = pvlib.irradiance.aoi(self.tilt, self.azimut, zenith, azimuth_sun)
        # GTI berechnen (vereinfachte Formel)
        theta_rad = np.radians(theta)
        tilt_rad = np.radians(self.tilt)
        cos_theta = np.cos(theta_rad)
        cos_beta = np.cos(tilt_rad)

        # Sicherstellen, dass keine negativen Werte in cos_theta und cos_beta sind
        cos_theta = np.maximum(cos_theta, 0)
        cos_beta = np.maximum(cos_beta, 0)

        GTI = GHI * (cos_theta + self.albedo * (1 - cos_beta) / 2)
        GTI = np.maximum(GTI, 0)

        # Verluste berücksichtigen
        degradation_factor = 1 - self.degradation_rate * self.age
        shading_factor = 1 - self.shading
        #temperaturverlust
        T_cell = T_air + (GTI / 800) *20
        gamma = -0.0045   #Temperaturkoeffizient für Siliziumzellen (Bsp.)
        temp_factor = 1 + gamma * (T_cell -25)
        #verschmutzungsgrad
        soil_factor = 1 - self.D_soil
        total_loss_factor = degradation_factor * shading_factor * temp_factor * soil_factor
 

        # Leistung berechnen (in kW) mit der Formel: P_el = GTI * A * total_loss
        pel_theoretical = GTI * self.size * total_loss_factor / 10e6
        pel = np.minimum(pel_theoretical, self.rated_power)

        return pel