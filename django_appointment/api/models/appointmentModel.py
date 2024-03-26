from django.db import models
from .locationModel import Location
from .doctorModel import *

class Appointment(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    STATUS_CHOICES = [
        ("Confirmed", 'Confirmed'),
        ("Cancelled", 'Cancelled'),
        ("Pending", 'Pending'),
        ("Rescheduled" , 'Rescheduled'),
        ("Completed" , 'Completed'),
    ]
    patientName = models.CharField(max_length=100, default=None)                                                                                        
    patientphoneNumber = models.IntegerField(default=None)
    patientEmail = models.EmailField(default=None)                                                      
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, null=True, blank=True)    
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField(default=None)
    day = models.IntegerField(choices=DAY_CHOICES, blank=True, default=None)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")   
    rescheduled_start_time = models.TimeField(null=True, blank=True)
    rescheduled_end_time = models.TimeField(null=True, blank=True)
    rescheduled_date = models.DateField(null=True, blank=True)
    rescheduled_day = models.IntegerField(choices=DAY_CHOICES, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.date:
            self.day = self.date.weekday()
        if self.rescheduled_date:
            self.rescheduled_day = self.rescheduled_date.weekday()
        super().save(*args, **kwargs)



