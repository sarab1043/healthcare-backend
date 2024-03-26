from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema, uritemplate
from rest_framework.viewsets import ModelViewSet

from api.services.user import UserService

userService = UserService()

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Login
        """
        result = userService.login(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
class SignupView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Signup
        """
        result = userService.signup(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
    
class ProfileView(APIView):

    def get(self, request, format=None):
        """
        Get Profile
        """
        result = userService.get_profile(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        """
        Update Profile
        """
        result = userService.update_profile(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Login With Google
        """
        result = userService.google_login(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = (AllowAny,)

    from rest_framework_simplejwt.authentication import JWTAuthentication
    authentication_classes = [JWTAuthentication]
    def get(self, request, format=None):
        """
        Logout user
        """
        result = userService.user_logout(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        Forgot password
        """
        result = userService.forgot_password(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, token, format=None):
        """
        Forgot password
        """
        result = userService.reset_password(request, token, format=None)
        return Response(result, status=status.HTTP_200_OK)

class ValidateTokenView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, token, format=None):
        """
        Validate token
        """
        result = userService.validate_token(request, token, format=None)
        return Response(result, status=status.HTTP_200_OK)