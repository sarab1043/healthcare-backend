from api.views import *
from django.urls import path, include
from django.conf import settings 
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import routers
from rest_framework import permissions
from rest_framework_simplejwt import views as jwt_views

app_name = 'api'

router = routers.DefaultRouter()

schema_view = get_schema_view(
    openapi.Info(
        title="Your API Name",
        default_version='v1',
        description="Your API description",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginView.as_view(), name="login"),
    path('google-login/', GoogleLoginView.as_view(), name="google-login"),
    path('signup/', SignupView.as_view(), name="signup"),
    path('forgotpassword/', ForgotPasswordView.as_view(), name="forgot-password"),
    path('resetpassword/<token>/', ResetPasswordView.as_view(), name="forgotpassword"),
    path('validate/<token>/', ValidateTokenView.as_view(), name="validatetoken"),
    path('logout/', LogoutView.as_view(), name="logout"),

    path('profile/', ProfileView.as_view(), name="profile"),
    path('doctor/availability/', AvailabilityView.as_view(), name="availability"),
    path('doctor/availability/weekly-hours/', WeeklyHoursAvailabilityView.as_view(), name="update-weekly-hours"),
    path('doctor/availability/date-specific/', DateSpecificAvailabilityView.as_view(), name="update-date-specific"),
    path('doctor/availability/date-specific/<id>/', DateSpecificAvailabilityView.as_view(), name="update-date-specific"),
    path('doctors/', GetAllDoctorsView.as_view(), name="get-all-doctors"),
    path('doctors/search/', SearchDoctors.as_view(), name='search-doctors'),
    path('doctor/appointments/', DoctorAppointmentView.as_view( ), name='get-all-appointments'),
    path('doctor/appointments/<id>/', DoctorAppointmentByIdView.as_view( ), name='get-appointments-by-id'),
    path('doctor/appointment-duration/', UpdateAppointmentDurationView.as_view(), name='update-appointment-duration'),

    path('patient/appointments/', PatientAppointmentView.as_view(), name="appointments-by-patient"),
    path('patient/records/', PatientRecordView.as_view(), name="patient-record"),
    path('patient/records/<id>/', PatientRecordByAptIdView.as_view(), name="patient-record-by-appointment-id"),

    path('specializations/', SpecializationListView.as_view() , name='specializations')

]