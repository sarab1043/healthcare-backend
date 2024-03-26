from abc import ABC, abstractmethod


class PatientBaseService(ABC):

    @abstractmethod
    def create_appointment(self):
        pass