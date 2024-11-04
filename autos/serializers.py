from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from autos.models import Run, Position, AthleteCoachRelation, ChallengeRecord


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


class ShortUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name']


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # Add a custom field
    runs_finished = serializers.SerializerMethodField()  # Add a custom field

    # runs_in_progress = serializers.SerializerMethodField()  # Add a custom field
    # runs_finished = serializers.IntegerField(source='runs_finished_count', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'runs_finished']

    def get_type(self, obj):
        if obj.is_staff:
            return 'coach'
        else:
            return 'athlete'

    def get_runs_finished(self, obj):
        # return obj.run_set.filter(status='finished').count()
        return Run.objects.filter(athlete_id=obj.id, status='finished').count()


class DetailAthleteSerializer(UserSerializer):
    coach = serializers.SerializerMethodField()

    def get_coach(self, obj):
        model = AthleteCoachRelation.objects.filter(athlete_id=obj.id).first()
        if model:
            return model.coach_id

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'coach']


class DetailCoachSerializer(UserSerializer):
    athletes = serializers.SerializerMethodField()

    def get_athletes(self, obj):
        athletes = AthleteCoachRelation.objects.filter(coach_id=obj.id).values_list('athlete_id', flat=True)
        return list(athletes)

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'runs_finished', 'athletes']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = ShortUserSerializer(read_only=True, source='athlete')

    class Meta:
        model = Run
        fields = ['id', 'comment', 'athlete', 'created_at', 'status', 'distance', 'run_time_seconds', 'speed',
                  'athlete_data']


class ChallengeRecordSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ChallengeRecord
        fields = ['athlete', 'name', 'id']

    def get_name(self, obj):
        return obj.get_name_display()
