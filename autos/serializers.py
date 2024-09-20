from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from autos.models import Run, Position


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):

    def validate_run(self, value):
        if not Run.objects.filter(id=value, status='in_progress').exists():
            raise ValidationError(f'Run {value} not started or already finished')

    class Meta:
        model = Position
        fields = ['id', 'run', 'longitude', 'latitude']
