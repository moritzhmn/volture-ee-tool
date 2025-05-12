from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    def __init__(self, name, location, weather_file):
        self.name = name
        self.location = location
        self.weather_file = weather_file

    @abstractmethod
    def simulate_power(self, weather_row):
        pass