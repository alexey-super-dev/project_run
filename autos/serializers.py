from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from autos.models import Run, Position


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    date_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f")

    def validate_run(self, value):
        if not Run.objects.filter(id=value.id, status='in_progress').exists():
            raise ValidationError(f'Run {value.id} not started or already finished')
        return value

    def validate_latitude(self, value):
        if not (-90 <= int(value) <= 90):
            raise ValidationError(f'Latitude {value} out of range')
        return value

    def validate_longitude(self, value):
        if not (-180 <= int(value) <= 180):
            raise ValidationError(f'Latitude {value} out of range')
        return value

    class Meta:
        model = Position
        fields = ['id', 'run', 'longitude', 'latitude', 'date_time', 'speed', 'distance']


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # Add a custom field

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type']

    def get_type(self, obj):
        if obj.is_staff:
            return 'coach'
        else:
            return 'athlete'
