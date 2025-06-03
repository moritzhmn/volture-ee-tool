from abc import ABC, abstractmethod

class BaseGenerator:
    def __init__(self, name, location, rated_power, case):
        self.name = name
        self.location = location
        self.rated_power = rated_power
        self.case = case

    @abstractmethod
    def simulate_power(self, weather_row):
        pass