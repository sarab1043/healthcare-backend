from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .locationModel import Location
from timezone_field import TimeZoneField
from django.db.models.signals import post_save
from django.dispatch import receiver

class Specialization(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
class DoctorProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qualification = models.TextField(null=True, blank=True)
    specializations = models.ManyToManyField(Specialization, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_slot_duration = models.IntegerField(default=45)

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    # def __str__(self):
    #     return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    day_of_week = models.IntegerField(choices=DAY_CHOICES, blank=True, null=True)  # Make it nullable
    timeslot = models.ManyToManyField(TimeSlot, blank=True, null=True)
    break_start_time = models.TimeField(null=True, blank=True)
    break_end_time = models.TimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    available = models.BooleanField(default=True)
    default_working_start_time = models.TimeField(default='09:00')
    default_working_end_time = models.TimeField(default='17:00')