from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from autos.models import Run, Position, AthleteCoachRelation, ChallengeRecord, AthleteInfo, CollectableItem


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


class CollectableItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectableItem
        fields = ['id', 'name', 'uid', 'value', 'latitude', 'longitude', 'picture']


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()  # Add a custom field
    # runs_finished = serializers.SerializerMethodField()  # Add a custom field

    # runs_in_progress = serializers.SerializerMethodField()  # Add a custom field
    runs_finished = serializers.SerializerMethodField()
    # runs_finished = serializers.IntegerField(source='runs_finished_count', read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'runs_finished', 'rating', 'date_joined']

    def get_rating(selff, obj):
        if hasattr(obj, 'average_rating'):
            if obj.average_rating:
                return float(obj.average_rating)

    def get_type(self, obj):
        if obj.is_staff:
            return 'coach'
        else:
            return 'athlete'

    def get_runs_finished(self, obj):
        return obj.run_set.filter(status='finished').count()



class DetailAthleteSerializer(UserSerializer):
    coach = serializers.SerializerMethodField()
    items = CollectableItemSerializer(many=True, read_only=True, source='collectable_items')

    def get_coach(self, obj):
        model = AthleteCoachRelation.objects.filter(athlete_id=obj.id).first()
        if model:
            return model.coach_id

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'coach', 'items']


def calculate_average(numbers):
    if not numbers:
        return 0  # Return 0 if the list is empty to avoid division by zero

    total_sum = sum(numbers)  # Calculate the sum of the list
    count = len(numbers)  # Get the number of elements in the list
    average = total_sum / count  # Calculate the average

    return average


class DetailCoachSerializer(UserSerializer):
    athletes = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    def get_athletes(self, obj):
        athletes = AthleteCoachRelation.objects.filter(coach_id=obj.id).values_list('athlete_id', flat=True)
        return list(athletes)

    def get_rating(self, obj):
        rating = None
        if AthleteCoachRelation.objects.filter(coach_id=obj.id, rate__isnull=False).exists():
            ratings = []
            for relation in AthleteCoachRelation.objects.filter(coach_id=obj.id):
                ratings.append(relation.rate)
            return float(calculate_average(ratings))
        return rating

    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'type', 'runs_finished', 'athletes', 'rating']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = ShortUserSerializer(read_only=True, source='athlete')

    class Meta:
        model = Run
        fields = ['id', 'comment', 'athlete', 'created_at', 'status', 'distance', 'run_time_seconds', 'speed',
                  'athlete_data', 'carbon_emission']

        # fields = ['id', 'comment', 'athlete', 'athlete_data']


class ChallengeRecordSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ChallengeRecord
        fields = ['athlete', 'full_name', 'id']

    def get_full_name(self, obj):
        return obj.get_name_display()


class ChallengeRecordsWithUsersSerializer(serializers.ModelSerializer):
    name_to_display = serializers.SerializerMethodField()
    athletes = serializers.SerializerMethodField()

    class Meta:
        model = ChallengeRecord
        fields = ['athletes', 'name_to_display', 'id']

    def get_name_to_display(self, obj):
        return obj.get_name_display()

    def get_athletes(self, obj):
        ids = set(list(ChallengeRecord.objects.filter(name=obj.name).values_list('athlete_id', flat=True)))
        return_list = []
        # for id in ids:
        users = User.objects.filter(id__in=ids)
            # if user:
        for user in users:
            return_list.append({'id': user.id, 'full_name': f'{user.first_name} {user.last_name}',
                                'username': user.username})
        return return_list


class AthleteInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteInfo
        fields = ['user_id', 'weight', 'goals']
