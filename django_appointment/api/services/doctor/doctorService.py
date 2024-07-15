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

    def get_doctor_working_days(self, request, format=None): 
        try:
            user = CustomUser.objects.get(email=request.user)
            doctor_profile = DoctorProfile.objects.get(user=user)
            availability_obj = DoctorAvailability.objects.filter(doctor=doctor_profile)
            serializer = DoctorWorkingDaysSerializer(availability_obj, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctor availability fetched successfully"})

        except DoctorProfile.DoesNotExist:
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

            if (apt_status == 'Rescheduled') and (appointment.status == 'Cancelled'):
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "This appointment is cancelled"}

            current_time = datetime.now()
            appointment_start_time = datetime.combine(appointment.date, appointment.start_time)
            three_hours_behind = appointment_start_time - timedelta(hours=3)
           

            if (current_time >= three_hours_behind):
                if apt_status not in ['Rescheduled', 'Cancelled']:
                    return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "The time limit to update the appointment has exceeded. You can only reschedule or cancel the appointment"}

            if apt_status == 'Rescheduled':
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
        
    def break_time_availability(self, request, format=None):
        try:
            print("request data", request.data)
            day_str = request.data.get('day', '').capitalize()
            break_start_time = request.data.get('break_start_time')
            break_end_time = request.data.get('break_end_time')

            if not day_str:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Day is required"}
            
            day_int = next((item[0] for item in DoctorAvailability.DAY_CHOICES if item[1].lower() == day_str.lower()), None)
            if day_int is None:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Invalid day"}
            
            if not break_start_time and break_end_time:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Invalid break time"}

            doctor_obj = DoctorProfile.objects.get(user=request.user)
            availability_obj = DoctorAvailability.objects.filter(day_of_week=day_int, doctor=doctor_obj).first()

            if not availability_obj:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not available on day"}
            
            #convert datetime strings to objects
            break_start_time = datetime.strptime(break_start_time, "%H:%M:%S").time()
            break_end_time = datetime.strptime(break_end_time, "%H:%M:%S").time()

            if Appointment.objects.filter(day= day_int, start_time = break_start_time, end_time = break_end_time).exists():
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Appointments exists in break time"}

            if (availability_obj.break_start_time == break_start_time) and (availability_obj.break_end_time == break_end_time):
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "No changes detected. Break time already up-to-date."}
            
            with transaction.atomic():  # Use atomic transaction to ensure consistency
                availability_obj.break_start_time = break_start_time
                availability_obj.break_end_time = break_end_time
                availability_obj.break_time_updated = True
                availability_obj.save()

                serializer = UpdateWeeklyAvailabilitySerializer(availability_obj)
                print(serializer.data)
                return {"data": serializer.data, "status": status.HTTP_200_OK, "success": "Break time updated successfully"}
                
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
            avt_obj.timeslot.all().delete()
            avt_obj.delete() 
            return {"data": None, "status": status.HTTP_200_OK, "success": "Deleted successfully"}
        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not found"})
        except DoctorAvailability.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Availability not found"})
        except:
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}
        
    def date_specific_available_slots(self, request, format=None):
        try:
            date = request.GET.get('date', '')
            if not date:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Date is required"}

            date_object = datetime.strptime(date, '%Y-%m-%d').date()

            doctor_profile = DoctorProfile.objects.get(user=request.user)
            doctor_availability = DoctorAvailability.objects.filter(day_of_week=date_object.weekday(), doctor=doctor_profile).first()

            if not doctor_availability:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor not available on this date"}

            doctor_appointments = Appointment.objects.filter(doctor=doctor_profile, date=date_object)

            default_start_time = datetime.strptime(str(doctor_availability.default_working_start_time), '%H:%M:%S')
            default_end_time = datetime.strptime(str(doctor_availability.default_working_end_time), '%H:%M:%S')

            break_start_time = None
            break_end_time = None
            if doctor_availability.break_start_time and doctor_availability.break_end_time:
                break_start_time = datetime.strptime(str(doctor_availability.break_start_time), '%H:%M:%S')
                break_end_time = datetime.strptime(str(doctor_availability.break_end_time), '%H:%M:%S')

            slot_duration = doctor_profile.appointment_slot_duration
            current_time = default_start_time

            # List of dictionaries for the entire schedule
            schedule = []
            while current_time < default_end_time:
                if break_start_time and break_end_time and break_start_time <= current_time < break_end_time:
                    current_time += timedelta(minutes=slot_duration)
                    continue

                slot_end_time = current_time + timedelta(minutes=slot_duration)
                schedule.append({
                    'start_time': current_time.strftime('%H:%M:%S'),
                    'end_time': slot_end_time.strftime('%H:%M:%S')
                })
                current_time += timedelta(minutes=slot_duration)

            # List of dictionaries for the existing appointments
            appointments = []
            for appointment in doctor_appointments:
                appointments.append({
                    'start_time': appointment.start_time.strftime('%H:%M:%S'),
                    'end_time': appointment.end_time.strftime('%H:%M:%S')
                })

            # Calculate available slots by removing appointments from schedule
            available_slots = []

            for schedule_slot in schedule:
                if schedule_slot not in appointments:
                    available_slots.append(schedule_slot)

            return {"data": available_slots, "status": status.HTTP_200_OK, "success": "Slots fetched successfully"}

        except DoctorProfile.DoesNotExist:
            return {"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"}
        except Exception as e:
            print("Error:", e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}


    def get_all_specialization(self, request, format=None):
        try:
            specializations = Specialization.objects.all()
            serializer = SpecializationSerializer(specializations, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Specializations fetched successfully"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        
    def get_all_qualifications(self, request, format=None):
        try:
            specializations = Qualifications.objects.all()
            serializer = QualificationSerializer(specializations, many=True)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Qualifications fetched successfully"})

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
    

    def get_doctor_by_id(self, request, id, format=None): 
        try:
            print(id)
            doctor_profile = DoctorProfile.objects.get(user = id)
            serializer = DoctorProfileSerializer(doctor_profile)
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctor fetched successfully"})

        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
    

    def get_doctor_availability_by_date(self, request, docid, date, format=None):
        try:
            doctor_profile = DoctorProfile.objects.get(user=docid)
            doc_avail_objs = DoctorAvailability.objects.filter(doctor=doctor_profile, date=date)

            # Fetch the appointment for the given doctor and date
            appointment = Appointment.objects.filter(doctor=doctor_profile, date=date, status__in=["Confirmed", "Rescheduled"])
            adjusted_availability= []
            for apt in appointment:
                print(apt)
                    # Add the adjusted availability slot to the list
                adjusted_availability.append({
                    "start_time": apt.start_time,
                    "end_time": apt.end_time
                })

            return {"data": adjusted_availability, "status": status.HTTP_200_OK, "success": "Doctor Availability fetched successfully"}

        except DoctorProfile.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "Doctor not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})


    def get_doctor_booked_slots(self, request, doc_id, format=None):
        try:
            user = CustomUser.objects.filter(id=doc_id).first()
            if not user:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User not found."})

            # getting day availablity time slots of doctor
            doctor_unavailabile_slots = DoctorAvailability.objects.filter(
                doctor__user=user)

            formatted_slots = []
            for doctor_unavailable_slot in doctor_unavailabile_slots:
                slots = TimeSlotSerializer(
                    doctor_unavailable_slot.timeslot.all(), many=True).data
                if not slots:
                    try:
                        day = doctor_unavailable_slot.date.strftime("%A") if doctor_unavailable_slot.date else doctor_unavailable_slot.DAY_CHOICES[doctor_unavailable_slot.day_of_week][1]
                    except:
                        day = ""
                    data = {
                        "date": doctor_unavailable_slot.date.strftime("%Y-%m-%d") if doctor_unavailable_slot.date else "",
                        "start_time": doctor_unavailable_slot.default_working_start_time,
                        "end_time": doctor_unavailable_slot.default_working_end_time,
                        "break_start_time": doctor_unavailable_slot.break_start_time,
                        "break_end_time": doctor_unavailable_slot.break_end_time,
                        "day": day,
                        "available" : doctor_unavailable_slot.available
                    }
                    formatted_slots.append(data)
                else:
                    for slot in slots:
                        date = doctor_unavailable_slot.date.strftime("%Y-%m-%d") if doctor_unavailable_slot.date else ""
                        try:
                            day = doctor_unavailable_slot.date.strftime("%A") if doctor_unavailable_slot.date else doctor_unavailable_slot.DAY_CHOICES[doctor_unavailable_slot.day_of_week][1]
                        except:
                            day = ""
     
                        data = {
                            "date": date,
                            "start_time": slot['start_time'],
                            "end_time": slot['end_time'],
                            "break_start_time": doctor_unavailable_slot.break_start_time,
                            "break_end_time": doctor_unavailable_slot.break_end_time,
                            "day": day,
                            "available" : doctor_unavailable_slot.available
                        }
                        if doctor_unavailable_slot.date:
                            weekday = doctor_unavailable_slot.date.weekday()
                            doctor_obj = DoctorAvailability.objects.get(day_of_week = weekday, doctor__user = user)
                            data["break_start_time"]= doctor_obj.break_start_time
                            data["break_end_time"]= doctor_obj.break_end_time

                        formatted_slots.append(data)

            appointments = Appointment.objects.filter(
                doctor__user=user).order_by('-created_at')
            serializer = DoctorBookedSlotsSerializer(appointments, many=True)
            serialized_data = serializer.data

            if serialized_data:
                formatted_slots.extend(serialized_data)
                data = formatted_slots
            else:
                data = formatted_slots

            return {"data": data, "status": status.HTTP_200_OK, "success": "Booked & Unavailable Slots fetched successfully"}

        except Exception as e:
            print("e", str(e))
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        
    def get_doctor_break_slots(self, request, doc_id, format=None):
        try:
            user = CustomUser.objects.filter(id=doc_id).first()
            if not user:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User not found."})

            # getting day availablity time slots of doctor
            doctor_availabile_slots = DoctorAvailability.objects.filter(
                doctor__user=user)

            data = DoctorBreakSlotSerializer(doctor_availabile_slots, many = True).data
            return {"data": data, "status": status.HTTP_200_OK, "success": "Break Slots fetched successfully"}

        except Exception as e:
            print("e", str(e))
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        

    def get_slot_duration(self, request, doc_id, format=None):
        try:
            user_profile = DoctorProfile.objects.filter(user__id = doc_id).first()
            if not user_profile:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User profile not found."})
            
            data = {
                "slot_duration":user_profile.appointment_slot_duration
            }
            return {"data": data, "status": status.HTTP_200_OK, "success": "Default slot duration fetched successfully"}

        except Exception as e:
            print("easdfsdfsdfsdf", str(e))
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        
    def update_slot_duration(self, request, format=None):
        try:
            slot_duration = request.data.get("slot_duration")

            if not slot_duration:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Slot duration not found."})
            
            user_profile = DoctorProfile.objects.filter(user = request.user).first()
            print(DoctorProfile,'DoctorProfile')
            if not user_profile:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User profile not found."})
            
            if user_profile.appointment_slot_duration == slot_duration:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "No changes detected. Slot duration already up-to-date."}

            # updating slot durations
            user_profile.appointment_slot_duration = slot_duration
            user_profile.save()


            ENUM = {
                30:{
                    "break_start_time":"13:00",
                    "break_end_time":"13:30"
                },
                40:{
                    "break_start_time":"12:20",
                    "break_end_time":"13:00"
                },
                45:{
                    "break_start_time":"12:45",
                    "break_end_time":"13:30"
                },
                50:{
                    "break_start_time":"13:10",
                    "break_end_time":"14:00"
                },
                60:{
                    "break_start_time":"12:00",
                    "break_end_time":"13:00"
                }
            }
            print(type(slot_duration))  

            print(ENUM[slot_duration]["break_start_time"])

            DoctorAvailability.objects.filter(date = None, doctor = user_profile).exclude(break_time_updated = True).update(break_start_time = ENUM[slot_duration]["break_start_time"],break_end_time = ENUM[slot_duration]["break_end_time"],)
            

            return {"data": [], "status": status.HTTP_200_OK, "success": "Default slot duration updated successfully"}

        except Exception as e:
            print("e", str(e))
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        

    def slug_profile(self, request, slug, format=None):
        try:
            slug_doc_profile = DoctorProfile.objects.filter(slug = slug)

            if not slug_doc_profile.exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor Profile not found."})
            
            if (slug_doc_profile.first().user.role == "Doctor"):
                serializer = DoctorProfileSerializer(slug_doc_profile.first(), context={'request': request})
                return {"data": serializer.data, "status": status.HTTP_200_OK, "success": "Doctor Profile fetched successfully"}
            else:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Doctor Profile not found."})

        except Exception as e:
            print("e", str(e))
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})
        
        
    def google_doctor_profile(self, request, format=None):
        try:

            if DoctorProfile.objects.filter(user = request.user).exists():
                print(request.data)
                user = CustomUser.objects.get(email=request.user)
                # print(user , type(user))
                serializer = UserLoginSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    print(serializer.errors)
                    return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

                if (user.role == "Doctor"):
                    doctor_profile = DoctorProfile.objects.get(user=user)
                    serializer = UpdateProfileSerializer(doctor_profile, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        print("doctor_profile_serializer", serializer.data)
                    else:
                        print(serializer.errors)
                        return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

                return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Profile updated successfully"})

            country = request.data.get('country')
            city = request.data.get('city')
            qualification = request.data.get('qualification')
            specializations = request.data.get('specializations')
            contactnumber = request.data.get('contactnumber')
    

            if not specializations or not qualification or not country or not city:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Specializations and qualifications are required."})

            specialization_ids = [spec_obj.id for spec_obj in [Specialization.objects.filter(name__iexact=specialization_name).first() for specialization_name in specializations] if spec_obj is not None]
            print(specialization_ids, 'specialization_ids')
            if not specialization_ids:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Specializations do not found"})
            
            user = CustomUser.objects.filter(id = request.user.id).first()
            with transaction.atomic():
                doctorprofile = DoctorProfile.objects.create(user=user, qualification=qualification)
                doctorprofile.specializations.set(specialization_ids)
                
                for day in range(0, 5):  # Monday to Friday
                    doctor_availability, created = DoctorAvailability.objects.get_or_create(doctor=doctorprofile, day_of_week=day)
                for day in range(5, 7):  # Monday to Friday
                    doctor_availability, created = DoctorAvailability.objects.get_or_create(doctor=doctorprofile, day_of_week=day, available=False)

                if contactnumber:
                    doctorprofile.contactnumber = contactnumber
                    doctorprofile.save()

                if city or country:
                    if Location.objects.filter(country__iexact = country, city__iexact = city).exists():
                        location = Location.objects.get(country__iexact = country,city__iexact = city)
                    else:
                        location = Location.objects.create(country=country.capitalize(), city=city.capitalize())
                    user.location = location
                    user.save()
                serializer = UserLoginSerializer(user)
                data = serializer.data
                return ({"data": data, "status": status.HTTP_201_CREATED, "success": "Doctor Profile Created"})
                
        except Exception as e:
                print("e", str(e))
                return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

           