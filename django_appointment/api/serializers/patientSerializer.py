from rest_framework import serializers
from api.models  import *

class PatientRecordSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = PatientRecord
        fields = "__all__"