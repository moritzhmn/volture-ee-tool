from models.base_generator import BaseGenerator

class PVModel(BaseGenerator):
    def __init__(self, name, panel_angle_deg, efficiency, location, weather_file):
        super().__init__(name, location, weather_file)
        self.panel_angle_deg = panel_angle_deg
        self.efficiency = efficiency

    def simulate_power(self, weather_row):
        irradiance = weather_row["irradiance"]
        return irradiance * self.efficiency