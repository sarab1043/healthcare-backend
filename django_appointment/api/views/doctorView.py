from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.services.doctor import DoctorService

doctorService = DoctorService()

class GetAllDoctorsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """
        Get All Doctors
        """
        result = doctorService.get_all_doctors(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class SearchDoctors(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """
        Get Doctors By Specialization
        """
        result = doctorService.search_doctors(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
class DoctorAppointmentView(APIView):
    # permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """
        Get Appointments by doctor
        """
        result = doctorService.get_appointments(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class AvailabilityView(APIView):

    def get(self, request, format=None):
        """
        Get Doctor's Available Hours
        """
        result = doctorService.get_availability(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class DoctorAppointmentByIdView(APIView):
    """
    Get Appointment By Id
    """
    def put(self, request, id, format=None):
        result = doctorService.update_appointment_status(request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)

class WeeklyHoursAvailabilityView(APIView):
    """
    Update Weekly Hours
    """
    def post(self, request, format=None):
        result = doctorService.weekly_hours_availability(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
    # def patch(self, request, id, format=None):
    #     result = doctorService.weekly_hours_availability(request,id, format=None)
    #     return Response(result, status=status.HTTP_200_OK)

class DateSpecificAvailabilityView(APIView):
    """
    Update Date Specific
    """
    def post(self, request, format=None):
        result = doctorService.date_specific_availability(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
    def delete(self, request, id, format=None):
        result = doctorService.delete_date_specific_availability(request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)

class SpecializationListView(APIView):
    permission_classes = (AllowAny,)

    """
    Get All Speciallizations
    """
    def get(self, request, format=None):
        result = doctorService.get_all_specialization(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    

class UpdateAppointmentDurationView(APIView):
    """
    Update Appointment Duration
    """
    def  put(self, request, format=None):
        result = doctorService.update_appointment_duration(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


class DoctorByIdView(APIView):
    permission_classes = (AllowAny,)
    """
    Get Doctor By Id
    """

    def get(self, request, id, format=None):
        result = doctorService.get_doctor_by_id(request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)