from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema, uritemplate
from rest_framework.viewsets import ModelViewSet

from api.services.appointment import AppointmentService

appointmentService = AppointmentService()

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Create Appointment
        """
        result = appointmentService.create_appointment(request, format=None)
        return Response(result, status=status.HTTP_200_OK)