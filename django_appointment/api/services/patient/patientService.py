from .patientBaseService import PatientBaseService
from rest_framework import status
from rest_framework.response import Response
import json
from django.http import JsonResponse
from api.serializers import *
import datetime 
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date
from django.db.models import F
from datetime import datetime, timedelta

class PatientService(PatientBaseService):

    def __init__(self):
        pass

    def create_appointment(self, request, format=None):
        try:
            print(request.user.id)
            required_params = ['country', 'city',  'specialization', 'doctor', 'start_time', 'end_time', 'date', 'patientName', 'patientphoneNumber', 'patientEmail']

            # Check if all required parameters are present
            missing_params = [param for param in required_params if param not in request.data]
            if missing_params:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": f"The following parameters are required: {', '.join(missing_params)}"})

            doctor = request.data['doctor']
            start_time = datetime.strptime(request.data['start_time'], '%H:%M:%S')
            end_time = datetime.strptime(request.data['end_time'], '%H:%M:%S')
            
            appointment_duration = end_time - start_time
            print(appointment_duration)
            doctor_obj = DoctorProfile.objects.get(user=doctor)

            if appointment_duration > timedelta(minutes=doctor_obj.appointment_slot_duration):
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Appointment duration exceeds slot duration"})

            country = request.data['country']
            city = request.data['city']
            specialization = request.data['specialization']
            patientName = request.data.get('patientName')
            patientphoneNumber = request.data.get('patientphoneNumber')
            patientEmail = request.data.get('patientEmail')
            start_time = request.data['start_time']
            end_time = request.data['end_time']
            date = request.data['date']
            day_of_week = datetime.strptime(date, '%Y-%m-%d').weekday()
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M:%S")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M:%S")
           
            loc_obj = Location.objects.get(country__iexact=country, city__iexact=city)
            specialization_obj = Specialization.objects.get(name__iexact=specialization)
            
            day_string = DoctorAvailability.objects.filter(day_of_week=day_of_week, available=True)
            if (end_datetime<datetime.now()): 
                 return ({
                    "data": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "error": "You cannot book appointments for past dates or times that have already passed."
                })

            slot_available = is_slot_available(self, doctor_obj, date, day_of_week, start_time, end_time)
            print("slot_available", slot_available)
            if not slot_available:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "success": "Doctor not available on this time slot"})

            if not DoctorProfile.objects.filter(user=doctor, specializations__name__iexact=specialization).exists() and CustomUser.objects.filter(id = doctor, location=loc_obj):
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})

            if Appointment.objects.filter(patientEmail = patientEmail, date=date, start_time__lt=end_time, end_time__gt=start_time, doctor=doctor_obj).exclude(Q(status="Cancelled") | Q(status="Completed")).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "You already have an appointment in between this slot"})
            
            if Appointment.objects.filter(doctor=doctor_obj, date=date, start_time__lt=end_time, end_time__gt=start_time).exclude(Q(status="Cancelled") | Q(status="Completed")).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not available on this time slot"})

           
            serializer = CreateAppointmentSerializer(data=request.data)
            if serializer.is_valid ():
                serializer.validated_data['location'] = loc_obj
                serializer.validated_data['specialization'] = specialization_obj
                serializer.validated_data['doctor'] = doctor_obj
                serializer.save ()
                data = serializer.data
                return ({"data": data, "status": status.HTTP_201_CREATED, "success": "Appointment saved"})
            print(serializer.errors)

        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})
        
        except Specialization.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found with this specialization"})
        
        except DoctorAvailability.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor is not available on this time"})
        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

        except Exception as e:
            print(e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def get_appointments(self, request, format=None):
        try:
            email = request.data.get('email')
            if not email:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Email is required"})

            appointments_obj = Appointment.objects.filter(patientEmail=email).order_by('-created_at')

            serializer = GetAppointmentSerializer(appointments_obj, many=True)
            return ({"data": serializer.data, "status": status.HTTP_201_CREATED, "success": "Appointment fetched successully"})

        except Exception as e:
            print("e", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def create_patient_record(self, request, format=None):
        try:
            if not request.data.get('appointment'):
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "appointment required"})

            doctor_obj = DoctorProfile.objects.get(user=request.user.id)
            print(doctor_obj)
            print(request.data['appointment'])
            appointment = Appointment.objects.get(doctor=doctor_obj, id=request.data['appointment'], status__in=['Confirmed', 'Rescheduled'])
            print(appointment)
            print(PatientRecord.objects.filter(appointment=appointment))
            if PatientRecord.objects.filter(appointment=appointment).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Patient record already exists for this apointment."})

            serializer = PatientRecordSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ({"data": None, "status": status.HTTP_201_CREATED, "success": "Patient record saved."})
            print(serializer.errors)

        except  DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found."})

        except Appointment.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Appointment not found."})

        except Exception as e:
            print(e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong."})

    def get_record_by_aptId(self, request, id, format=None):
        try:
            # Retrieve the appointment
            appointment = Appointment.objects.get(id=id)

            if request.user.email == appointment.patientEmail or request.user.email == appointment.doctor.user.email:
                # Check if the appointment is confirmed or rescheduled
               record_obj = PatientRecord.objects.get(appointment=id)
               serializer = PatientRecordSerializers(record_obj)
               return ({"data": serializer.data, "status": status.HTTP_201_CREATED, "success": "Appointment fetched successully"})
            else:
                return {"data": None, "status": status.HTTP_403_FORBIDDEN, "error": "You are not authorized to access this appointment."}

        except Appointment.DoesNotExist:
            return {"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "Appointment not found."}

        except Exception as e:
            print(e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong."}

        

def is_slot_available(self, doctor_obj, date, day_of_week, start_time, end_time):
    try:
        availability_working_hours= DoctorAvailability.objects.filter(Q(day_of_week=day_of_week) | Q(date=date)).filter(
                    default_working_start_time__lte=start_time,
                    default_working_end_time__gte=end_time
                )
        if not availability_working_hours:
            return False
        
        date_specific_availability = DoctorAvailability.objects.filter(doctor=doctor_obj, date=date)
        if date_specific_availability:
            # if DoctorAvailability.objects.filter(doctor=doctor_obj, date=date).filter( Q(timeslot__isnull=True, available=False) | Q(available=True, timeslot__start_time__lte=start_time, timeslot__end_time__gte=end_time)).exists():
            if DoctorAvailability.objects.filter(doctor=doctor_obj, date=date).filter( Q(timeslot__isnull=True, available=False) | Q(available=True, timeslot__start_time__lte=start_time, timeslot__end_time__gte=end_time)).exists():
                return False
            else:
                return True
        elif DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__isnull=True).exists():
            if not DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, default_working_start_time__lt=end_time, default_working_end_time__gt=start_time, available=True).exists():
                return False
            return True

        elif not DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=True):
            return False
        else:
            return True
    except Exception as e:
        print("eeeeeeeeee", e)


