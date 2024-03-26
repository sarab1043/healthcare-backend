from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .locationModel import Location
from .appointmentModel import Appointment
from timezone_field import TimeZoneField


class PatientRecord(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    subjective = models.TextField(null=True, blank=True)
    assessment = models.TextField(null=True, blank=True)
    plan=models.TextField(null=True, blank=True)
    symptoms = models.TextField(null=True, blank=True)
    medical_history = models.TextField(null=True, blank=True)
    family_history = models.TextField(null=True, blank=True)
    social_history = models.TextField(null=True, blank=True)
    review_symptoms = models.TextField(null=True, blank=True)
    chief_complaint = models.TextField(null=True, blank=True)
    objective = models.TextField(null=True, blank=True)
    physical_examination = models.TextField(null=True, blank=True)
    diagnostic_test = models.TextField(null=True, blank=True)
    objective_medications = models.TextField(null=True, blank=True)
    patient_history = models.TextField(null=True, blank=True)
    vital_signs = models.TextField(null=True, blank=True)
    impressions = models.TextField(null=True, blank=True)
    further_testing = models.TextField(null=True, blank=True)
    objective_prognosis = models.TextField(null=True, blank=True)
    diagnosis = models.TextField(null=True, blank=True)
    plan_medications = models.TextField(null=True, blank=True)
    follow_up_care = models.TextField(null=True, blank=True)
    patient_education = models.TextField(null=True, blank=True)
    plan_prognosis = models.TextField(null=True, blank=True)
    treatment_plan = models.TextField(null=True, blank=True)

