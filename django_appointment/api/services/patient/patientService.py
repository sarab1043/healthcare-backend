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
        
            country = request.data['country']
            city = request.data['city']
            specialization = request.data['specialization']
            doctor = request.data['doctor']
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
            doctor_obj = DoctorProfile.objects.get(user=doctor)
            
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
            # availability_working_hours= DoctorAvailability.objects.filter(Q(day_of_week=day_of_week) | Q(date=date)).filter(
            #     default_working_start_time__lte=start_time,
            #     default_working_end_time__gte=end_time
            # )
            # if not availability_working_hours:
            #     return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            # date_specific_availability = DoctorAvailability.objects.filter(doctor=doctor_obj, date=date)
            # if date_specific_availability:
            #     print("con1")
            #     if DoctorAvailability.objects.filter(date=date, timeslot__isnull=True, available=False).exists():
            #         print("con2")
            #         return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
                
            #     elif DoctorAvailability.objects.filter(date=date, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=False).exists():
            #         print("con3")
            #         return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            # elif DoctorAvailability.objects.filter(day_of_week=day_of_week, timeslot__isnull=True).exists():
            #     print("con4")
            #     if DoctorAvailability.objects.filter(day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=False).exists():
            #         print("con5")
            #         return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            # elif not DoctorAvailability.objects.filter(day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=True):
            #     return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})


            if not DoctorProfile.objects.filter(user=doctor, location=loc_obj, specializations__name__iexact=specialization).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})

            if Appointment.objects.filter(patientEmail = patientEmail, start_time__lt=end_time, end_time__gt=start_time, doctor=doctor_obj).exclude(Q(status="Cancelled") | Q(status="Completed")).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "You already have an appointment in between this slot"})
            
            if Appointment.objects.filter(doctor=doctor_obj, start_time__lt=end_time, end_time__gt=start_time).exclude(Q(status="Cancelled") | Q(status="Completed")).exists():
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

        except DoctorAvailability.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor is not available on this time"})
        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

        except Exception as e:
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


def is_slot_available(self, doctor_obj, date, day_of_week, start_time, end_time):
    try:
        print("fn called")
        print(day_of_week)
        print(doctor_obj)
        print("date", date)
        print("start time", start_time)
        print("end time", end_time)
        # print(DoctorAvailability.objects.filter(day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=False))

        print("doc avail", DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=False))
        print("null", DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__isnull=True))
        availability_working_hours= DoctorAvailability.objects.filter(Q(day_of_week=day_of_week) | Q(date=date)).filter(
                    default_working_start_time__lte=start_time,
                    default_working_end_time__gte=end_time
                )
        if not availability_working_hours:
            print("not avail working hours")
            # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            return False
        
        date_specific_availability = DoctorAvailability.objects.filter(doctor=doctor_obj, date=date)
        if date_specific_availability:
            print("date specific")
            # print("1", DoctorAvailability.objects.filter(doctor=doctor_obj, date=date, timeslot__isnull=True, available=False))
            # print("2", DoctorAvailability.objects.filter(doctor=doctor_obj, date=date, available=True).filter(Q(timeslot__start_time__lte=start_time) & Q(timeslot__end_time__gte=end_time)))
            # if DoctorAvailability.objects.filter(doctor=doctor_obj, date=date, timeslot__isnull=True, available=False).exists():
            #     print("con1")
            #     return False
            #     # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            # elif not DoctorAvailability.objects.filter(doctor=doctor_obj, date=date, available=True).filter(Q(timeslot__start_time__lte=start_time) & Q(timeslot__end_time__gte=end_time)).exists():
            #     print("con2")
            #     return False
            #     # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            # else:
            #     print("else condition")
            #     return True

            if DoctorAvailability.objects.filter(doctor=doctor_obj, date=date).filter( Q(timeslot__isnull=True, available=False) | ~Q(available=True, timeslot__start_time__lte=start_time, timeslot__end_time__gte=end_time)).exists():
                return False
            else:
                return True


        elif DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__isnull=True).exists():
        #     print("con3")
            if not DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, default_working_start_time__lt=end_time, default_working_end_time__gt=start_time, available=True).exists():
                return False
                # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
            return True

        elif not DoctorAvailability.objects.filter(doctor=doctor_obj, day_of_week=day_of_week, timeslot__start_time__lt=end_time, timeslot__end_time__gt=start_time, available=True):
            print("con5")
            return False
            # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "message": "Doctor not available on this time slot"})
        else:
            return True
    except Exception as e:
        print("eeeeeeeeee", e)


