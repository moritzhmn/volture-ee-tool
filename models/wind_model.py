from .base_generator import BaseGenerator
from .cp_interpolation import get_turbine_power # Funktion zum Abruf von cp basierend auf Klasse + Windgeschwindigkeit

class WindModel(BaseGenerator):
    def __init__(
        self,
        name,
        rated_power,
        cut_in,
        cut_out,
        rated_speed,
        rotor_radius,
        hub_height,
        alpha=0.2,
        wake_loss=0.10,
        location=None,
        turbines_count=1
    ):
        super().__init__(name, location)
        self.rated_power = rated_power  # Gesamtleistung des Parks in kW
        self.cut_in = cut_in
        self.cut_out = cut_out
        self.rated_speed = rated_speed
        self.rotor_radius = rotor_radius
        self.hub_height = hub_height
        self.alpha = alpha
        self.wake_loss = wake_loss
        self.air_density = 1.225  # kg/m³ Standardluftdichte
        self.turbines_count = turbines_count
        
        # Nennleistung pro Turbine
        self.turbine_rated_power = self.rated_power / self.turbines_count
        
        # Turbinenklasse bestimmen
        self.turbine_class = self.classify_turbine(self.turbine_rated_power)
        print(self.turbine_class)

    def classify_turbine(self, rated_power_mw):
        if rated_power_mw < 1:
            return '<1 MW'
        elif rated_power_mw < 2:
            return '1-2 MW'
        elif rated_power_mw < 2.3:
            return '2.0–2.3 MW'
        elif rated_power_mw < 2.6:
            return '2.3–2.6 MW'
        elif rated_power_mw < 3.0:
            return '2.6–3.0 MW'
        elif rated_power_mw < 3.3:
            return '3.0–3.3 MW'
        elif rated_power_mw < 3.7:
            return '3.3–3.7 MW'
        elif rated_power_mw < 5.2:
            return '3.7–5.2 MW'
        else:
            return '>=5.2 MW'
        

    def adjust_wind_speed(self, v_ref, ref_height=10):
        """Windgeschwindigkeit auf Nabenhöhe skalieren"""
        return v_ref * (self.hub_height / ref_height) ** self.alpha

    def simulate_power(self, weather_row):
     v_ref = weather_row["wind_speed"]
     print(f"Referenz-Windgeschwindigkeit (10m): {v_ref:.2f} m/s")

     v = self.adjust_wind_speed(v_ref)
     print(f"Windgeschwindigkeit auf Nabenhöhe (adjusted): {v:.2f} m/s")

     if v < self.cut_in or v > self.cut_out:
        print(f"Windgeschwindigkeit {v:.2f} m/s außerhalb des Betriebsbereichs ({self.cut_in}-{self.cut_out} m/s). Leistung = 0")
        return 0

    # Wake-Verlust berücksichtigen
     v_eff = v * (1 - self.wake_loss)
     print(f"Effektive Windgeschwindigkeit nach Wake-Verlust ({self.wake_loss*100:.1f}%): {v_eff:.2f} m/s")
     
     #Windleistung in aktuellen Modell nicht notwendig
     #swept_area = 3.1416 * self.rotor_radius ** 2  # A = π * R²
     #print(f"Rotorfläche: {swept_area:.2f} m²")

     #p_wind = 0.5 * self.air_density * swept_area * v_eff ** 3
     #print(f"Leistung Wind (theoretisch): {p_wind:.2f} W")

    # cp aus get_cp() nach Turbinenklasse und effektiver Windgeschwindigkeit
     p_turbine = get_turbine_power(self.turbine_class, v_eff) / 1e6
     print(f"Leistung pro Turbine vor Begrenzung: {p_turbine:.2f} MW")

    # Leistung pro Turbine darf Nennleistung nicht überschreiten
     p_turbine = min(p_turbine, self.turbine_rated_power) 
     print(f"Leistung pro Turbine nach Begrenzung auf Nennleistung ({self.turbine_rated_power} MW): {p_turbine:.2f} MW")

    # Gesamtleistung Windpark
     total_power = p_turbine * self.turbines_count
     print(f"Gesamtleistung Windpark vor Systemverlusten: {total_power:.2f} MW")

    # Verluste durch Einspeisung, Umrichter etc.
     system_efficiency_factor = 1 - 0.015 - 0.03 - 0.01
     total_power *= system_efficiency_factor
     print(f"Gesamtleistung Windpark nach Systemverlusten: {total_power:.2f} MW")

     return total_power