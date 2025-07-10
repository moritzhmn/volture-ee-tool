from .base_generator import BaseGenerator
import pvlib
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from pvlib.irradiance import erbs

geolocator = Nominatim(user_agent="volture_reverse")

#PV Modell Klasse definieren mit Eigenschaften aus Base Generator und Zusätzlichen wie z.B. albedo, PVModel erbt alle Methoden und Eigenschaften von BaseGenerator
class PVModel(BaseGenerator):
    #Geolocator wird mit User Agent angelegt
    geolocator = Nominatim(user_agent="volture_ee")

    def __init__(
        self,
        name,
        rated_power,      
        location,
        case,        
        albedo=None,
        azimuth=None,
        tilt=None,
        k_g=None,
        k_t=None
    ):
        # Falls location ein Ortsname ist, erst umwandeln mit Hilfe von get_ta_long Methode
        if isinstance(location, str):
            coords = self.get_lat_lon(location)
            if coords is None:
                raise ValueError(f"Ort '{location}' konnte nicht gefunden werden.")
            location = coords
        
        #Übergibt alle notwenidgen Paramter an die Basisklasse
        super().__init__(name, location, rated_power, case)
        
        #Definiert Standardwerte falls nicht vorhanden 
        self.azimuth = azimuth if azimuth is not None else 180
        self.tilt = tilt if tilt is not None else 30
        self.albedo = albedo if albedo is not None else 0.2
        
        # Location umwandeln falls String
        if isinstance(location, str):
            coords = self.get_lat_lon(location)
            if coords is None:
                raise ValueError(f"Ort '{location}' konnte nicht gefunden werden.")
            self.location = coords
        else:
            self.location = location

    #Aus string Location Umwandlung in Lat,Lon
    @classmethod
    def get_lat_lon(cls, place_name):
        location = cls.geolocator.geocode(place_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None

    #Ermittelt Generatorkorrekturfakor anhand des Zeitpunkt und Szenario   
    @staticmethod
    def get_k_g(timestamp,case):
        #Definiert Generatorkorrekturfaktoren für Szenarien Referenz: Heinrich Häberlin "Photovoltaik"
        k_g_list_worst =[0.44,0.32,0.66,0.74,0.76,0.74,0.74,0.74,0.78,0.76,0.48,0.38] #geringe Werte in Wintermonaten bei hoher Schneelast
        k_g_list_normal = [0.7,0.74,0.81,0.82,0.83,0.83,0.83,0.83,0.83,0.82,0.72,0.65]
        k_g_list_best = [0.86,0.90,0.91,0.91,0.91,0.91,0.91,0.91,0.91,0.89,0.85,0.83]
        #Extrahiert Monat aus ausgewähltem Referenzdatum 
        month = timestamp.month

        if case == 'best':
         k_g = k_g_list_best[month-1]
        elif case == 'worst':
         k_g = k_g_list_worst[month-1]   
        elif case == 'normal':
         k_g = k_g_list_normal[month-1] 
        else:
            raise ValueError(f"Kein Eintrag gefunden für Case '{case}'")
        return k_g
    
    #Ermittelt Generatorkorrekturfakor anhand des Zeitpunkt
    @staticmethod 
    def get_k_t(timestamp):
        #Definiert Temperaturkorrekturfaktor für freistehende Anlgen eher gering (PV-Parks als Referenzanwendung im allgemeinen gering) Referenz: Heinrich Häberlin "Photovoltaik"
        month = timestamp.month
        k_t_list = [1.06,1.05,1.03,1.00,0.97,0.95,0.95,0.96,0.99,1.01,1.04,1.06]

        k_t = k_t_list[month-1]
        return k_t
    
    #Ermittelt Systemwirkungsgrad (System: Trafo, Umrichter, Kabel etc.)
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
    

    #Hauptmethode zur PV-Leistungssimulation 
# Hauptmethode zur PV-Leistungssimulation 
    def simulate_power(self, weather_row):
        # Extrahiert GHI aus Wetterdaten
        h_g_10min = weather_row.get("pv", None)
        if h_g_10min is None:
            raise ValueError("Globalstrahlung nicht im Wetterdatensatz gefunden")
        ghi = (h_g_10min * 10000) / 600
        # Extrahiert Zeit aus Wetterdaten
        timestamp = pd.to_datetime(weather_row["datetime"])

        # Warnung bei GHI = 0 zwischen 10–15 Uhr
        if 10 <= timestamp.hour <= 15 and ghi == 0:
            print(f"Warnung: Globalstrahlung ist 0 bei {timestamp}")

        latitude, longitude = self.location
        site = pvlib.location.Location(latitude, longitude)

        solpos = site.get_solarposition(timestamp)
        zenith = solpos['zenith'].iloc[0] if hasattr(solpos['zenith'], 'iloc') else solpos['zenith']
        azimuth_sun = solpos['azimuth'].iloc[0] if hasattr(solpos['azimuth'], 'iloc') else solpos['azimuth']

        ghi_scalar = float(ghi)
        dni_dhi = erbs(ghi_scalar, zenith, timestamp.dayofyear)
        dni = dni_dhi["dni"]
        dhi = dni_dhi["dhi"]


        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            dni=dni,
            ghi=ghi_scalar,
            dhi=dhi,
            solar_zenith=zenith,
            solar_azimuth=azimuth_sun,
            albedo=self.albedo
        )["poa_global"]

        if hasattr(poa, 'values'):
            poa = poa.values[0]


        P_stc = self.rated_power  # z.B. 100000 für 100 kW
        G_0 = 1000  # Referenzbestrahlung in W/m²

        k_g = self.get_k_g(timestamp, self.case)
        k_t = self.get_k_t(timestamp)
        eta_sys = self.get_eta_sys(self.case)
        PR = k_g * k_t * eta_sys

        

        P_t = P_stc * (poa / G_0) * PR
        P_t = max(P_t, 0)
        return P_t