from abc import ABC, abstractmethod


class DoctorBaseService(ABC):

    @abstractmethod
    def get_appointments(self):
        pass