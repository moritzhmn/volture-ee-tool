from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    def __init__(self, name, location):
        self.name = name
        self.location = location

    @abstractmethod
    def simulate_power(self, weather_row):
        pass