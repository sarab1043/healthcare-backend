from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.services.patient import PatientService

patientService = PatientService()

class PatientAppointmentView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """
        Get Appointment
        """
        result = patientService.get_appointments(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


    def post(self, request, format=None):
        """
        Create Appointment
        """
        result = patientService.create_appointment(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    

class AppointmentRecordByAptIdView(APIView):
    def get(self, request, id, format=None):
        """ 
        Get Appointment Record
        """
        result = patientService.get_appointment_detail(
            request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
    def post(self, request, id, format=None):
        """ 
        Get Appointment Record
        """
        result = patientService.confirm_appointment_status(
            request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)

class PatientRecordByAptIdView(APIView):

    def get(self, request, id, format=None):
        """
        Get Appointment
        """
        result = patientService.get_record_by_aptId(request, id, format=None)
        return Response(result, status=status.HTTP_200_OK)


   
    
class PatientRecordView(APIView):
    
    def get(self, request, format=None):
        """
        Get PatientRecord
        """
        result = patientService.get_patient_record(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


    def post(self, request, format=None):
        """
        Create PatientRecord
        """
        result = patientService.create_patient_record(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
    def put(self, request, pk, format=None):
        """
        Update PatientRecord
        """
        result = patientService.update_patient_record(request, pk ,format=None)
        return Response(result, status=status.HTTP_200_OK)