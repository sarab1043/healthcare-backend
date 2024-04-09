from .doctorBaseService import DoctorBaseService
from rest_framework import status
from rest_framework.response import Response
import json
from django.http import JsonResponse
from api.serializers import *
import datetime
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from ..patient import patientService
from django.db.models import Q

class DoctorService(DoctorBaseService):

    def __init__(self):
        pass
    
    def get_all_doctors(self, request, format=None):
        try:
            doctors = DoctorProfile.objects.all()
            serializer = DoctorProfileSerializer(doctors, many=True, context={'request': request})
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctors fetched successfully"})
        except Exception as e:
            print(e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def search_doctors(self, request, format=None):
        try:
            specialization = request.query_params.get('specialization')
            city = request.query_params.get('city')
            country = request.query_params.get('country')

            doctors = DoctorProfile.objects.all()
            if specialization:
                doctors = doctors.filter(specializations__name__iexact=specialization)
            if city:
                doctors = doctors.filter(user__location__city__iexact=city)
            if country:
                doctors = doctors.filter(user__location__country__iexact=country)
            serializer = DoctorProfileSerializer(doctors, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctors fetched successfully"})

        except Exception as e:
            print(e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def get_appointments(self, request, format=None):
        try:
            user = CustomUser.objects.get(email=request.user)
            doctor_profile = DoctorProfile.objects.get(user=user)
            appointments_obj = Appointment.objects.filter(doctor=doctor_profile.id)
            serializer = GetAppointmentSerializer(appointments_obj, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Appointments fetched successfully"})

        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "User not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def get_availability(self, request, format=None): 
        try:
            user = CustomUser.objects.get(email=request.user)
            doctor_profile = DoctorProfile.objects.get(user=user)
            availability_obj = DoctorAvailability.objects.filter(doctor=doctor_profile)
            serializer = DoctorAvailabilitySerializer(availability_obj, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctor availability fetched successfully"})

        except doctor_profile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
    
    def update_appointment_status(self, request, id, format=None):
        try:
            print("rqst data", request.data)
            user = CustomUser.objects.get(email=request.user)
            doctor_obj = DoctorProfile.objects.get(user=user)
            appointment = Appointment.objects.get(id=id, doctor=doctor_obj)
            apt_status = request.data.get('status')


            if not apt_status:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Status is required"}

            if (apt_status == 'Cancelled') and (appointment.status == 'Cancelled'):
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "This appointment is already Cancelled"}
            
            if (apt_status == 'Confirmed') and (appointment.status != 'Pending'):
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "This appointment may already be confirmed"}

            current_time = datetime.now()
            appointment_start_time = datetime.combine(appointment.date, appointment.start_time)
            three_hours_behind = appointment_start_time - timedelta(hours=3)
            rescheduled_start_time_str = request.data.get('start_time')
            rescheduled_end_time_str = request.data.get('end_time')

            # Convert string representations to datetime.time objects
            rescheduled_start_time = datetime.strptime(rescheduled_start_time_str, '%H:%M:%S').time()
            rescheduled_end_time = datetime.strptime(rescheduled_end_time_str, '%H:%M:%S').time()
            rescheduled_date = request.data.get('date')

            start_time = appointment.start_time
            end_time = appointment.end_time
            date = appointment.date
            day_of_week = appointment.day

            if (current_time >= three_hours_behind):
                if apt_status not in ['Rescheduled', 'Cancelled']:
                    return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "The time limit to update the appointment has exceeded. You can only reschedule or cancel the appointment"}

            if apt_status == 'Rescheduled' or (apt_status == 'Confirmed' and appointment.status == 'Pending'):

                if apt_status == 'Rescheduled' and not rescheduled_start_time and not rescheduled_end_time and not rescheduled_date:
                    return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Resheduled start and end time required"}
                
                if rescheduled_date and rescheduled_start_time and rescheduled_end_time:
                    date = rescheduled_date
                    start_time = rescheduled_start_time
                    end_time = rescheduled_end_time
                    day_of_week = datetime.strptime(rescheduled_date, '%Y-%m-%d').weekday()

                    # Convert time strings to datetime objects
                    start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M:%S")
                    end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M:%S")
                    day_string = DoctorAvailability.objects.filter(day_of_week=day_of_week, available=True)

                    if end_datetime < datetime.now(): 
                        return {
                            "data": None,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "error": "You cannot book appointments for past dates or times that have already passed."
                        }
                    
                    # Calculate appointment duration
                    appointment_duration = end_datetime - start_datetime
                    if appointment_duration > timedelta(minutes=doctor_obj.appointment_slot_duration):
                        return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Appointment duration exceeds slot duration"}

                    request.data['start_time'] = rescheduled_start_time
                    request.data['end_time'] = rescheduled_end_time
                    request.data['date'] = rescheduled_date

                slot_available = patientService.is_slot_available(self, doctor_obj, date, day_of_week, start_time, end_time)
                
                print("slot_available", slot_available)
                if not slot_available:
                    print("slot not avail")
                    return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "You are not available on this time slot"})

                if Appointment.objects.filter(
                    doctor=doctor_obj
                    ).filter(
                        Q(date=date, start_time__lt=end_time, end_time__gt=start_time)  & 
                        (Q(status="Rescheduled") | Q(status="Confirmed"))
                    ).exclude(Q(status="Cancelled") | Q(status="Completed") | Q(status="Pending")).exists():
                    return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Your slot for this time is already booked."}

                if Appointment.objects.filter(
                    patientEmail=appointment.patientEmail
                    ).filter(
                        Q(date=date, start_time__lt=end_time, end_time__gt=start_time)  & 
                        (Q(status="Rescheduled") | Q(status="Confirmed"))
                    ).exclude(Q(status="Cancelled") | Q(status="Completed") | Q(status="Pending")).exists():
                    return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Patient already has an appointment scheduled for this time slot"}

            
            serializer = UpdateAppointmentSerializer(appointment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Appoinment updated successfully"})

            print("serializer.errors", serializer.errors)

        except Appointment.DoesNotExist:
            return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "Appointment not found"})

        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "Doctor not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def weekly_hours_availability(self, request, format=None):
        try:
            print("request data", request.data)
            day_str = request.data.get('day', '').capitalize()
            default_working_start_time = request.data.get('default_working_start_time')
            default_working_end_time = request.data.get('default_working_end_time')

            if not day_str:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Day is required"}
            
            day_int = next((item[0] for item in DoctorAvailability.DAY_CHOICES if item[1].lower() == day_str.lower()), None)
            if day_int is None:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Invalid day"}
            
            doctor_obj = DoctorProfile.objects.get(user=request.user.id)
            availability_obj, created = DoctorAvailability.objects.get_or_create(day_of_week=day_int, doctor=doctor_obj)
            
            with transaction.atomic():  # Use atomic transaction to ensure consistency
                timeslots_data = request.data.get('timeslots', [])
                
                if timeslots_data:  # Check if timeslots are provided in the request
                    timeslot_ids = []
                    
                    for timeslot_data in timeslots_data:
                        try:
                            timeslot = TimeSlot.objects.get(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
                        except TimeSlot.DoesNotExist:
                            timeslot = TimeSlot.objects.create(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
                        
                        timeslot_ids.append(timeslot.id)
                    
                    # Clear existing timeslots not in the request data
                    if not created:  # Only clear slots if availability object already exists
                        availability_obj.timeslot.clear()
                    
                    # Add or update timeslots from request data
                    availability_obj.timeslot.add(*timeslot_ids)
                
                if default_working_start_time and default_working_end_time:
                    # Clear existing timeslots
                    availability_obj.timeslot.clear()

                if request.data.get('available') == False:
                    availability_obj.timeslot.clear()

                serializer = UpdateWeeklyAvailabilitySerializer(availability_obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    print(serializer.data)
                    return {"data": serializer.data, "status": status.HTTP_200_OK, "success": "Slot updated successfully"}
                print(serializer.errors)
                
        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"})
        
        except Exception as e:
            print("Error:", e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}
        

    # def weekly_hours_availability(self, request, id, format=None):
    #     try:
    #         print(request.data)
    #         timeslot_ids = []  # Create an empty list to store the primary keys of timeslots
    #         for timeslot_data in request.data['timeslots']:
    #             try:
    #                 timeslot = TimeSlot.objects.get(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
    #                 timeslot_ids.append(timeslot.id)  # Append the primary key to the list
    #             except TimeSlot.DoesNotExist:
    #                 timeslot = TimeSlot.objects.create(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
    #                 timeslot_ids.append(timeslot.id)  # Append the primary key to the list

    #         request.data['timeslot'] = timeslot_ids
    #         doctor_obj = DoctorProfile.objects.get(user=request.user.id)
    #         availability = DoctorAvailability.objects.get(id=id, doctor=doctor_obj)

    #         serializer = UpdateWeeklyAvailabilitySerializer(availability, data=request.data, partial=True)
    #         if serializer.is_valid():
    #             serializer.save()
    #             return ({"data": serializer.data, "status": status.HTTP_200_OK, "message": "Slot updated successfully"})
    #         print(serializer.errors)
    #     except DoctorProfile.DoesNotExist:
    #         return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "message": "Doctor Slot not found"})

    #     except DoctorAvailability.DoesNotExist:
    #         return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "message": "Available Slot not found"})

    #     except Exception as e:
    #         print("eeeeee", e)
    #         return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "Something went wrong"})
    
    def date_specific_availability(self, request, format=None):
        try:
            date = request.data.get('date', '')
            print("date",date)
            if not date:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Date is required"}
        
            doctor_obj = DoctorProfile.objects.get(user=request.user.id)
            availability_obj, created = DoctorAvailability.objects.get_or_create(date=date, doctor=doctor_obj)
            
            with transaction.atomic():  # Use atomic transaction to ensure consistency
                timeslots_data = request.data.get('timeslots', [])
                
                if timeslots_data:  # Check if timeslots are provided in the request
                    timeslot_ids = []
                    
                    for timeslot_data in timeslots_data:
                        try:
                            timeslot = TimeSlot.objects.get(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
                        except TimeSlot.DoesNotExist:
                            timeslot = TimeSlot.objects.create(start_time=timeslot_data['start_time'], end_time=timeslot_data['end_time'])
                        
                        timeslot_ids.append(timeslot.id)
                    
                    # Clear existing timeslots not in the request data
                    if not created:  # Only clear slots if availability object already exists
                        availability_obj.timeslot.clear()
                    
                    # Add or update timeslots from request data
                    availability_obj.timeslot.add(*timeslot_ids)

                    if request.data.get('available') == False:
                        print("this condition gets true")
                        availability_obj.timeslot.clear()

                serializer = UpdateTimeSpecificAvailabilitySerializer(availability_obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return {"data": serializer.data, "status": status.HTTP_200_OK, "success": "Slot updated successfully"}
                print(serializer.errors)
                
        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"})
        
        except Exception as e:
            print("Error:", e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}

    def delete_date_specific_availability(self, request, id,  format=None):
        try:
            doctor_obj = DoctorProfile.objects.get(user=request.user.id)
            avt_obj = DoctorAvailability.objects.get(id=id, doctor=doctor_obj)
            avt_obj.delete() 
            return {"data": None, "status": status.HTTP_200_OK, "success": "Deleted successfully"}
        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})
        except DoctorAvailability.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Availability not found"})
        except:
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}

    def get_all_specialization(self, request, format=None):
        try:
            specializations = Specialization.objects.all()
            serializer = SpecializationSerializer(specializations, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Specializations fetched successfully"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        

    def update_appointment_duration(self, request, format=None):
        try:
            appointment_slot_duration = request.data.get("appointment_slot_duration")
            doctor_obj = DoctorProfile.objects.get(user=request.user.id)
            
            if not appointment_slot_duration:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "appointment_slot_duration is required"}

            serializer = UpdateAppointmentDurationSerializer(doctor_obj, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return {"data": serializer.data, "status": status.HTTP_200_OK, "success": "Appointment duration updated successfully"}
            
        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})
        except Exception as e:
            print(e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}
