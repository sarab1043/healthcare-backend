from rest_framework import serializers
from api.models  import *
from .userSerializer import *
from rest_framework.exceptions import ValidationError

class DayOfWeekField(serializers.Field):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    def to_representation(self, value):
        return dict(self.DAY_CHOICES).get(value, '')

class GetAppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorProfileSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)  
    location = LocationSerializers(read_only=True)
    day = DayOfWeekField()
    # rescheduled_day = DayOfWeekField()

    class Meta:
        model = Appointment
        fields = "__all__"

class UpdateAppointmentSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Appointment
        fields = "__all__"


class CreateAppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorProfileSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)  
    location = LocationSerializers(read_only=True)
   
    class Meta:
        model = Appointment
        fields = "__all__"

class UpdateAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields= "__all__"

    