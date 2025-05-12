from .base_generator import BaseGenerator

class WindModel(BaseGenerator):
    def __init__(self, name, rated_power, cut_in, cut_out, rated_speed, location):
        super().__init__(name, location)
        self.rated_power = rated_power
        self.cut_in = cut_in
        self.cut_out = cut_out
        self.rated_speed = rated_speed

    def simulate_power(self, weather_row):
        v = weather_row["wind_speed"]
        if v < self.cut_in or v > self.cut_out:
            return 0
        elif v < self.rated_speed:
            return self.rated_power * ((v - self.cut_in) / (self.rated_speed - self.cut_in)) ** 3
        else:
            return self.rated_power