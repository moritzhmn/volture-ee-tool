from .base_generator import BaseGenerator
from .cp_interpolation import get_cp

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
        turbines_count=1  # Anzahl der Turbinen im Windpark
    ):
        super().__init__(name, location)
        self.rated_power = rated_power  # Gesamtleistung des Windparks (in kW)
        self.cut_in = cut_in
        self.cut_out = cut_out
        self.rated_speed = rated_speed
        self.rotor_radius = rotor_radius
        self.hub_height = hub_height
        self.alpha = alpha
        self.wake_loss = wake_loss
        self.air_density = 1.225  # kg/m³, Standardwert
        self.turbines_count = turbines_count  # Anzahl der Turbinen im Windpark
        
        # Berechne die Einzel-Nennleistung jeder Turbine im Park
        self.turbine_rated_power = self.rated_power / self.turbines_count

    def adjust_wind_speed(self, v_ref, ref_height=10):
        """Skaliere Windgeschwindigkeit auf Nabenhöhe."""
        return v_ref * (self.hub_height / ref_height) ** self.alpha

    def simulate_power(self, weather_row):
        v_ref = weather_row["wind_speed"]
        v = self.adjust_wind_speed(v_ref)

        if v < self.cut_in or v > self.cut_out:
            return 0

        swept_area = 3.1416 * self.rotor_radius ** 2  # A = π * R²
        p_wind = 0.5 * self.air_density * swept_area * v ** 3

        # Einfaches c_p-Modell
        cp = get_cp(v)

        p_turbine = (cp * p_wind * (1 - self.wake_loss)) / 1000000  # Leistung in kW (Watt in kW)

        # Die Leistung jeder Turbine darf die Nennleistung nicht überschreiten
        p_turbine = min(p_turbine, self.turbine_rated_power)

        # Gesamtleistung des Windparks (Anzahl der Turbinen berücksichtigen)
        total_power = p_turbine * self.turbines_count

        # Gesamte Windpark-Leistung unter Berücksichtigung des Wake-Effekts
        total_power *= (1 - self.wake_loss)

        return total_power