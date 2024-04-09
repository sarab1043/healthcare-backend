from rest_framework import serializers
from api.models  import *
# from api.
class LocationSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = Location
        fields = "__all__"

class UserLoginSerializer(serializers.ModelSerializer):
    location = LocationSerializers(read_only=True)
    class Meta:
        model = CustomUser
        exclude = ['password', 'user_permissions', 'groups']

class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = "__all__"

class UpdateProfileSerializer(serializers.ModelSerializer):
    user = UserLoginSerializer(read_only=True)  
    class Meta:
        model = DoctorProfile
        fields = "__all__"

class TimeSlotSerializer(serializers.ModelSerializer):
    # start_time_12h = serializers.SerializerMethodField()
    # end_time_12h = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = '__all__'

    # def get_start_time_12h(self, obj):
    #     return obj.start_time.strftime("%I:%M %p")  # Format start time in 12-hour format
    
    # def get_end_time_12h(self, obj):
    #     return obj.end_time.strftime("%I:%M %p")'
        

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    timeslot = TimeSlotSerializer(read_only=True, many=True)
    day_of_week = serializers.CharField(source='get_day_of_week_display')
    # default_working_start_time = serializers.SerializerMethodField()
    # default_working_end_time = serializers.SerializerMethodField()
    class Meta:
        model = DoctorAvailability
        fields = ('id', 'timeslot', 'day_of_week', 'date', 'break_start_time', 'break_end_time', 'description', 'available', 'doctor', 'default_working_start_time', 'default_working_end_time')


    # def get_default_working_start_time(self, obj):
    #     return obj.default_working_start_time.strftime("%I:%M %p")  # Format start time in 12-hour format
    
    # def get_default_working_end_time(self, obj):
    #     return obj.default_working_end_time.strftime("%I:%M %p")'
        
class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserLoginSerializer(read_only=True)  
    specializations = SpecializationSerializer(read_only=True, many=True)    
    availabilities = DoctorAvailabilitySerializer(source='doctoravailability_set', many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = "__all__"
    
class UpdateWeeklyAvailabilitySerializer(serializers.ModelSerializer):
    timeslot = TimeSlotSerializer(read_only=True, many=True)

    class Meta:
        model = DoctorAvailability
        fields = ('id', 'timeslot', 'break_start_time', 'break_end_time', 'description', 'available', 'default_working_start_time', 'default_working_end_time')

    
class UpdateTimeSpecificAvailabilitySerializer(serializers.ModelSerializer):
    timeslot = TimeSlotSerializer(read_only=True, many=True)

    class Meta:
        model = DoctorAvailability
        fields = ('id', 'timeslot', 'date', 'break_start_time', 'break_end_time', 'description', 'available')

class UpdateAppointmentDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ('appointment_slot_duration',)