from __future__ import print_function

from .userBaseService import UserBaseService
from rest_framework import status
from rest_framework.response import Response
import json
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from api.serializers.userSerializer import *
from django.db.models import Q
import datetime
import pytz
from datetime import datetime, timedelta
from rest_framework.exceptions import AuthenticationFailed
from google.auth.transport import requests
from google.oauth2 import id_token
from django.contrib.auth import logout
import time
import base64
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.core.mail import EmailMessage
import secrets
from django.utils.timezone import localtime


class UserService(UserBaseService):
    """
    Allow any user (authenticated or not) to access this url 
    """

    def __init__(self):
        pass

    def login(self, request, format=None):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            country = request.data.get('country')
            city = request.data.get('city')
            qualification = request.data.get('qualification')
            specializations = request.data.get('specializations')

            if not email and not password:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Email and Password required"})
            
            user_obj = CustomUser.objects.filter(email=email)
            if not user_obj:
                return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "User do not found"})

            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                serializer = UserLoginSerializer(user)
                refresh = RefreshToken.for_user(user)
                data = serializer.data
                data['token'] = str(refresh)
                return ({"data": data, "status": status.HTTP_200_OK, "success": "User login successfully"})
            else:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Invalid Credentials"})

        except Exception as e:
            print("eeeeee", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def signup(self, request, format=None):
        print("signup called", request.data)
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            country = request.data.get('country')
            city = request.data.get('city')
            qualification = request.data.get('qualification')
            specializations = request.data.get('specializations')
            fullname = request.data.get('fullname')
            contactnumber = request.data.get('contactnumber'),
            gender= request.data.get('gender')
            role=request.data.get('role')
            
                
            required_params = ['email', 'password', 'role']
            missing_params = [param for param in required_params if param not in request.data]

            if CustomUser.objects.filter(email=email).exists():
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User with this email already exist"})

            if missing_params:
                # return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": f"The following parameters are required: {', '.join(missing_params)}"})
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": f"The following parameters are required: {', '.join(missing_params)}", "redirectUrl": "/missing-params"});
            user = CustomUser.objects.create_user(email=email, password=password, role=role)
            if (role == 'Doctor'):
                if not specializations or not qualification or not country or not city:
                    return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Specializations and qualifications are required."})
               

                specialization_ids = [spec_obj.id for spec_obj in [Specialization.objects.filter(name__iexact=specialization_name).first() for specialization_name in specializations] if spec_obj is not None]
                if not specialization_ids:
                    return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Specializations do not found"})

                
                doctorprofile = DoctorProfile.objects.create(user=user, qualification=qualification)
                doctorprofile.specializations.set(specialization_ids)
               
                for day in range(0, 5):  # Monday to Friday
                    doctor_availability, created = DoctorAvailability.objects.get_or_create(doctor=doctorprofile, day_of_week=day)
                if fullname:
                    doctorprofile.fullname = fullname
                    doctorprofile.save()
                if contactnumber:
                    doctorprofile.contactnumber = contactnumber
                    doctorprofile.save()

            if fullname:
                    user.fullname = fullname
                    user.save()
            if gender:
                user.gender = gender
                user.save()

            if city or country:
                if Location.objects.filter(country__iexact = country, city__iexact = city).exists():
                    location = Location.objects.get(country__iexact = country,city__iexact = city)
                else:
                    location = Location.objects.create(country=country.capitalize(), city=city.capitalize())
            user.location = location
            user.save()
            serializer = UserLoginSerializer(user)
            refresh = RefreshToken.for_user(user)
            data = serializer.data
            data['token'] = str(refresh)
            return ({"data": data, "status": status.HTTP_201_CREATED, "success": "User created successfully"})
        
        except Exception as e:
            print("eeeeeeeeeee", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def get_profile(self, request, format=None):
        try:
            user = CustomUser.objects.get(email = request.user)
            doctor_profile = DoctorProfile.objects.get(user = user)
            serializer = DoctorProfileSerializer(doctor_profile, context={'request': request})
            return ({"data": serializer.data, "status": status.HTTP_200_OK, "success": "Profile fetched successfully"})
        except User.DoesNotExist:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "User not found"})
        except Exception as e:
            print("eeeeee", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def update_profile(self, request, format=None):
        try:
            print(request.data)
            user = CustomUser.objects.get(email=request.user)
            doctor_profile = DoctorProfile.objects.get(user=user)

            user_serializer = UserLoginSerializer(user, data=request.data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

            doctor_profile_serializer = UpdateProfileSerializer(doctor_profile, data=request.data, partial=True)
            if doctor_profile_serializer.is_valid():
                print("valid")
                doctor_profile_serializer.save()
                print("doctor_profile_serializer", doctor_profile_serializer.data)
            else:
                return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

            return ({"data": doctor_profile_serializer.data, "status": status.HTTP_200_OK, "success": "Profile updated successfully"})

        except User.DoesNotExist:
            return ({"data": None, "status": status.HTTP_401_UNAUTHORIZED, "error": "User not found"})

        except Exception as e:
            print("Error:", e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def google_login(self, request, format=None):
        try:
            access_token = request.data.get('access_token')
            if not access_token:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Access token required"})

            google_user_data = id_token.verify_oauth2_token(access_token, requests.Request())
            print(google_user_data)
            if "accounts.google.com" in google_user_data['iss']:
                try:
                    if google_user_data['aud'] != settings.GOOGLE_CLIENT_ID:
                        raise AuthenticationFailed(detail="Could not verify user")
                    email=google_user_data['email']
                    first_name=google_user_data['given_name']
                    last_name=google_user_data['family_name']
                    fullname=google_user_data['name']
                    provider = "Google"
                    user = CustomUser.objects.filter(email=email)
                    print(user)
                    if user.exists():
                        print("user exists")
                        user = authenticate(request, email=email, password=settings.SOCIAL_AUTH_PASSWORD)
                        if user is not None:
                            login(request, user)
                            serializer = UserLoginSerializer(user)
                            refresh = AccessToken.for_user(user)
                            data = serializer.data
                            data['token'] = str(refresh)
                            return ({"data": data, "status": status.HTTP_200_OK, "success": "User login successfully"})
                    else:
                        user = CustomUser.objects.create_user(email=email, password=settings.SOCIAL_AUTH_PASSWORD)
                        user.username = fullname
                        user.first_name = fullname
                        user.last_name = last_name
                        user.fullname = first_name  + ' '+ last_name
                        user.provider = provider
                        user.save()
                        doctorprofile = DoctorProfile.objects.create(user=user)
                        serializer = UserLoginSerializer(user)
                        refresh = AccessToken.for_user(user)
                        data = serializer.data
                        print("data",data)
                        data['token'] = str(refresh)
                        return ({"data": data, "status": status.HTTP_201_CREATED, "success": "User created successfully"})

                except Exception as e:
                    print(e)
                    return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Token in invalid or has expired"})
            else:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Token in invalid or has expired"})

        except Exception as e:
            print(e, "eeee")
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def user_logout(self, request, format=None):
        try:
            user = request.user
            if user:
                Refresh_token = request.data["refresh"]
                try:
                    token = RefreshToken(Refresh_token)
                except:
                    return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Token is invalid or expired"})

                token.blacklist()
                return ({"data": [], "status": status.HTTP_200_OK, "success": "Logged Out successfully"})
            else:
                return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "User do not found"})
        except Exception as e:
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def forgot_password(self, request, format=None):
        user_email = request.data.get('email')
        if not user_email:
            return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Email is required"})

        try:
            user = CustomUser.objects.get(email=user_email)
            send_password_reset_email(user)
            return ({"data": [], "status": status.HTTP_200_OK, "success": "Email sent successfuly. Please check you email"})

        except CustomUser.DoesNotExist:
            return ({"data": None, "status": status.HTTP_404_NOT_FOUND, "error": "User not found"})
        
        except Exception as e:
            print(e)
            return ({"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"})

    def reset_password(self, request, token, format=None):
        try:
            new_password = request.data.get("new_password")
            email = request.data.get("email")

            if not new_password and email:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Both email and new_password is required"}


            is_valid = validate_token_fn(token, email)
            print("is_valid", is_valid)
            if not is_valid:
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Token is not valid or has expired"}

            
            valid_token = PasswordResetToken.objects.get(token=token)
            user_obj = valid_token.user

            if user_obj.check_password(new_password):
                return {"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "New password should be different from the current password"}
            
            user_obj.set_password(new_password)
            user_obj.save()
            valid_token.delete()
            
            return {"data": None, "status": status.HTTP_200_OK, "success": "Password reset successfully"}
        
        except Exception as e:
            print("Exception occurred:", e)
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}

    def validate_token(self, request, token, format=None):
        try:
            print(request.data)
            email = request.data.get("email")
            if not email:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Email required"})

            token_is_valid = validate_token_fn(token, email)
            if not token_is_valid:
                return ({"data": None, "status": status.HTTP_400_BAD_REQUEST, "error": "Token is invalid or expired"})
            else:
                return ({"data": None, "status": status.HTTP_200_OK, "success": "Token is valid"})

        except Exception as e:
            return {"data": None, "status": status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Something went wrong"}

def validate_token_fn(token, email):
    try:
        user = CustomUser.objects.get(email=email)
        print(user)
        valid_token = PasswordResetToken.objects.get(token=token, user=user)
        print("valid token email", valid_token.user)
        print("valid_token",valid_token)
        user_obj = valid_token.user
        current_time = timezone.now()
        link_expire_time =  valid_token.created_at + timedelta(hours=2)
        if link_expire_time < current_time:
            print("i am here")
            return False
        return True
    
    except CustomUser.DoesNotExist:
        return False

    except PasswordResetToken.DoesNotExist:
        return False
    except Exception as e:
        print(e)
        return False
            

def send_password_reset_email(user):
    try:
        token = PasswordResetToken.objects.get(user=user)
        token.token = secrets.token_urlsafe(64)
        token.created_at = datetime.now()
        token.save()
        token_to_send = token.token
    except PasswordResetToken.DoesNotExist:
        new_token = secrets.token_urlsafe(64)
        token = PasswordResetToken.objects.create(user=user, token=new_token)
        token.created_at = datetime.now()
        token.save()
        token_to_send = new_token

    reset_link = f'http://localhost:8080/resetPassword/{token_to_send}'

    # Compose the email error
    subject = 'Password Reset'
    error = f'Hi {user.email},\n\nYou have requested to reset your password. Please click the following link to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.\n\nRegards,\nThe VoicePing Team'
    from_email = settings.EMAIL_HOST_USER
    
    try:
        email = EmailMessage(
            subject=subject,
            body=error,
            from_email=from_email,
            to=[user.email]  
        )
        email.send()
        return True
    except Exception as e:
        raise Exception('Failed to send the password reset email')



    