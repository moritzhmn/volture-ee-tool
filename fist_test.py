import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Standortklasse ---
class Standort:
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon

    def simuliere_wetter(self, zeiten):
        """ Dummy-Wettersimulation je nach Standort (z. B. durch Phasenverschiebung) """
        faktor = (hash(self.name) % 100) / 100
        globalstrahlung = 1000 * np.maximum(0, np.sin(np.linspace(0, 2 * np.pi, len(zeiten)) + faktor))
        windspeed = 6 + 2 * np.sin(np.linspace(0, 2 * np.pi, len(zeiten)) + faktor)
        return globalstrahlung, windspeed

# --- PV- und Windanlagen wie gehabt ---
class PVAnlage:
    def __init__(self, name, peak_power_kw, neigung, azimut, standort: Standort, wirkungsgrad=0.9):
        self.name = name
        self.peak_power_kw = peak_power_kw
        self.neigung = neigung
        self.azimut = azimut
        self.standort = standort
        self.wirkungsgrad = wirkungsgrad

    def leistung(self, globalstrahlung):
        return self.peak_power_kw * (globalstrahlung / 1000) * self.wirkungsgrad


class WindAnlage:
    def __init__(self, name, rated_power_kw, cut_in, cut_out, rated_speed, standort: Standort):
        self.name = name
        self.rated_power_kw = rated_power_kw
        self.cut_in = cut_in
        self.cut_out = cut_out
        self.rated_speed = rated_speed
        self.standort = standort

    def leistung(self, windspeed):
        if windspeed < self.cut_in or windspeed > self.cut_out:
            return 0
        elif windspeed < self.rated_speed:
            return self.rated_power_kw * (windspeed / self.rated_speed) ** 3
        else:
            return self.rated_power_kw

# --- Simulation für mehrere Standorte ---
def simuliere_netze(anlagen, zeiten):
    daten = pd.DataFrame(index=zeiten)
    wetter_cache = {}

    for anlage in anlagen:
        standort = anlage.standort.name

        # Wetterdaten je Standort nur einmal berechnen
        if standort not in wetter_cache:
            gs, ws = anlage.standort.simuliere_wetter(zeiten)
            wetter_cache[standort] = {'globalstrahlung': gs, 'windspeed': ws}

        wetter = wetter_cache[standort]
        if isinstance(anlage, PVAnlage):
            daten[anlage.name] = [anlage.leistung(g) for g in wetter['globalstrahlung']]
        elif isinstance(anlage, WindAnlage):
            daten[anlage.name] = [anlage.leistung(w) for w in wetter['windspeed']]

    daten['Gesamtleistung'] = daten.sum(axis=1)
    return daten

# --- Beispielnutzung ---
if __name__ == "__main__":
    zeiten = pd.date_range("2025-06-01 06:00", "2025-06-01 20:00", freq="15min")

    # Standorte
    berlin = Standort("Berlin", 52.5, 13.4)
    muenchen = Standort("Muenchen", 48.1, 11.6)
    kiel = Standort("Kiel", 54.3, 10.1)

    # Anlagen je Standort
    anlagen = [
        PVAnlage("PV_Berlin", 100, 30, 180, berlin),
        PVAnlage("PV_Muenchen", 150, 25, 190, muenchen),
        WindAnlage("Wind_Kiel", 3000, 3, 25, 12, kiel),
        WindAnlage("Wind_Berlin", 2500, 3, 25, 11, berlin),
    ]

    # Simulation starten
    daten = simuliere_netze(anlagen, zeiten)

    # Plot
    daten.plot(title="Leistungsverläufe an mehreren Standorten")
    plt.xlabel("Zeit")
    plt.ylabel("Leistung (kW)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()