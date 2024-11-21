import json

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max, Sum, Avg, F

from django.db.models import Sum, Count, Q, Avg, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from geopy.distance import geodesic
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .logic import calculate_run_time_by_id, calculate_run_time, calculate_run_time_different_way, calculate_median, \
    call_carboninterface
from .models import Autos, Run, Position, AthleteCoachRelation, ChallengeRecord  # Ensure the Autos model is imported
from .serializers import RunSerializer, PositionSerializer, UserSerializer, DetailAthleteSerializer, \
    DetailCoachSerializer, ChallengeRecordSerializer, ChallengeRecordsWithUsersSerializer


def get_autos(request):
    autos = Autos.objects.all()
    # Set safe=False to allow a non-dict object (list) to be serialized
    return JsonResponse([{'name': auto.name} for auto in autos], safe=False)


def subscribe_to_coach_api_url(request, id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=id)

    # Ensure the identified user is a coach
    if not coach.is_staff:
        return JsonResponse({'status': False, 'error': 'Можно подписываться только на Юзеров с типом Coach'},
                            status=400)

    try:
        # Parse the JSON request body
        data = json.loads(request.body)
        athlete_id = data.get('athlete', None)

        # Get the athlete by the ID provided in the body
        athlete = User.objects.filter(id=athlete_id).first()
        if not athlete:
            return JsonResponse({'status': False, }, status=400)

        if athlete.is_staff:
            return JsonResponse({'status': False, 'error': 'Подписываются могут только Юзеры с типом Athlete'},
                                status=400)
        if AthleteCoachRelation.objects.filter(athlete=athlete, coach=coach).exists():
            return JsonResponse({'status': False}, status=400)

        AthleteCoachRelation.objects.create(athlete=athlete, coach=coach)

        # Return success response
        return JsonResponse(
            {'status': True, 'message': f'{athlete.username} successfully subscribed to {coach.username}'})

    except (json.JSONDecodeError, TypeError, KeyError):
        return JsonResponse({'status': False, 'error': 'Invalid request format'}, status=400)

    except ValidationError as e:
        return JsonResponse({'status': False, 'error': str(e)}, status=400)


def get_company_details(request):
    details = {
        'company_name': 'Run Project',
        'slogan': 'Run or Die',
        'contacts': 'You know how to find us'
    }
    return JsonResponse(details)


class RunsViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all().select_related('athlete')
    serializer_class = RunSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'id']
    # filterset_fields = ['status']
    ordering_fields = ['created_at']

    @action(detail=True, methods=['post'], url_path='start')
    def start_run(self, request, pk=None):
        full_url = request.build_absolute_uri()
        run = self.get_object()  # Получить объект Run по ID из URL

        if run.status == 'in_progress':
            return Response({'status': 'already run'}, status=status.HTTP_400_BAD_REQUEST)

        if run.status == 'finished':
            return Response({'status': 'already stopped'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'in_progress'  # Например, метод start() запускает ваш объект
        run.save()
        return Response({'status': full_url}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='stop')
    def stop_run(self, request, pk=None):
        try:
            run = Run.objects.get(pk=pk)
        except Run.DoesNotExist:
            return Response({'error': 'Run not found'}, status=status.HTTP_404_NOT_FOUND)

        if run.status != 'in_progress':
            return Response({'status': 'Run not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'finished'
        run.save()

        # Assuming positions_list is your QuerySet:
        positions_list = Position.objects.filter(run=run).values('latitude', 'longitude')

        # Convert to list of tuples
        running_routes = [
            (position['latitude'], position['longitude'])
            for position in positions_list
        ]

        total_distance = 0
        for i in range(len(running_routes) - 1):
            start = running_routes[i]
            end = running_routes[i + 1]
            distance = geodesic(start, end).kilometers
            total_distance += distance

        run.distance = round(total_distance, 2)
        # run.speed = calculate_median(list(Position.objects.filter(run=run).values_list('speed', flat=True)))
        if Position.objects.filter(run=run).exists():
            run.speed = round(calculate_median(list(Position.objects.filter(run=run).values_list('speed', flat=True))),
                              2)
            # run.run_time_seconds = calculate_run_time_by_id(run)
            run.run_time_seconds = calculate_run_time_different_way(run)

        # run.carbon_emission = call_carboninterface(settings.CARBON_INTERFACE_API_KEY, run.distance)
        run.save()

        if Run.objects.filter(athlete_id=run.athlete_id, status='finished').count() == 10:
            ChallengeRecord.objects.create(athlete_id=run.athlete_id, name='RUN_10')

        if Run.objects.filter(athlete_id=run.athlete_id, status='finished').aggregate(dis=Sum('distance')).get('dis',
                                                                                                               None) > 50:
            ChallengeRecord.objects.get_or_create(athlete_id=run.athlete_id, name='RUN_50')

        if (run.run_time_seconds and run.run_time_seconds <= 600) and (run.distance and run.distance >= 2):
            ChallengeRecord.objects.get_or_create(athlete_id=run.athlete_id, name='RUN_2_10')

        return Response({'status': 'run stopped'}, status=status.HTTP_200_OK)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.filter()
    serializer_class = PositionSerializer

    def get_queryset(self):
        queryset = Position.objects.all()
        run = self.request.query_params.get('run', None)
        if run:
            queryset = queryset.filter(run=run)
        return queryset

    def perform_create(self, serializer):
        position = serializer.save()

        date_time = position.date_time
        try:
            previous_position = Position.objects.filter(run_id=position.run_id, date_time__lt=date_time).latest(
                'date_time')
            # previous_position = Position.objects.filter(run_id=position.run_id).exclude(id=position.id).latest('date_time')
        except Position.DoesNotExist:
            return

        start = (previous_position.latitude, previous_position.longitude)
        end = (position.latitude, position.longitude)
        distance = geodesic(start, end).kilometers
        if not distance:
            return
        timing = position.date_time - previous_position.date_time
        time_seconds = timing.total_seconds()
        if time_seconds > 0:
            speed_mps = distance * 1000 / time_seconds
            position.speed = round(speed_mps, 2)

        position.distance = round(distance, 2) + previous_position.distance
        position.save()
        return position


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            user = self.get_object()
            if user.is_staff:
                return DetailCoachSerializer
            return DetailAthleteSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Exclude superusers from the queryset
        queryset = queryset.filter(is_superuser=False)

        # Get the 'type' query parameter
        user_type = self.request.query_params.get('type', None)

        # Annotate runs_finished_count for all users
        queryset = queryset.annotate(
            runs_finished_count=Count('run', filter=Q(run__status='finished'))
        )

        # If filtering for coaches, annotate average_rating
        if user_type == 'coach':
            queryset = queryset.filter(is_staff=True)
            # queryset = queryset.annotate(average_rating=Avg('coaches__rate'))

        elif user_type == 'athlete':
            queryset = queryset.filter(is_staff=False)

        queryset = queryset.annotate(average_rating=Avg('coaches__rate'))
        return queryset


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChallengeRecord.objects.all()
    serializer_class = ChallengeRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['athlete', 'name']


# def get_challenges_summary(request): # 8
#     result = []
#     for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
#         data = {'name_to_display': challenge_type[1], 'athletes': []}
#         users_info = ChallengeRecord.objects.filter(name=challenge_type[0]).select_related('athlete').values('athlete_id',
#                                                                                                           'athlete__first_name',
#                                                                                                           'athlete__last_name')
#         for info in users_info:
#             data['athletes'].append({'full_name': f'{info['athlete__first_name']} {info['athlete__last_name']}',
#                                      'id': info['athlete_id']})
#         result.append(data)
#         # return result # TODO
#     return JsonResponse(result, safe=False)


# def get_challenges_summary(request): # 10
#     data = ChallengeRecordsWithUsersSerializer(instance=ChallengeRecord.objects.all(), many=True).data
#     return JsonResponse(data, safe=False)

# def get_challenges_summary(request): # 9
#     result = []
#     for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
#         data = {'name_to_display': challenge_type[1], 'athletes': []}
#         ids = set(list(ChallengeRecord.objects.filter(name=challenge_type[0]).values_list('athlete_id', flat=True)))
#         return_list = []
#         users = User.objects.filter(id__in=ids)
#         for user in users:
#             return_list.append({'id': user.id, 'full_name': f'{user.first_name} {user.last_name}'})
#         data['athletes'] = return_list
#         result.append(data)
#
#     return JsonResponse(result, safe=False)

#
# def get_challenges_summary(request): # 6
#     result = []
#     for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
#         data = {'name_to_display': challenge_type[1], 'athletes': []}
#         challenge_records = ChallengeRecord.objects.filter(name=challenge_type[0])
#         users_info = User.objects.filter(challenges__in=challenge_records)
#
#         for user in users_info:
#             data['athletes'].append({'full_name': f'{user.first_name} {user.last_name}', 'id': user.id})
#
#         result.append(data)
#
#     return JsonResponse(result, safe=False)

def get_challenges_summary(request):  # 6
    result = []
    for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
        data = {'name_to_display': challenge_type[1], 'athletes': []}
        users_info = User.objects.filter(challenges__name=challenge_type[0])
        for user in users_info:
            data['athletes'].append({'full_name': f'{user.first_name} {user.last_name}', 'id': user.id})
        result.append(data)
    return JsonResponse(result, safe=False)


# from django.http import JsonResponse
# from django.db.models import Prefetch
#
# def get_challenges_summary(request): # 5
#     # Prefetch related users for all challenge records
#     challenge_records = ChallengeRecord.objects.prefetch_related(
#         Prefetch('athlete', queryset=User.objects.only('id', 'first_name', 'last_name'))
#     ).all()
#
#     # Use a dictionary to organize data by challenge type
#     challenges_by_type = {}
#     for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
#         challenges_by_type[challenge_type[0]] = {
#             'name_to_display': challenge_type[1],
#             'athletes': []
#         }
#
#     # Populate the athletes for each challenge type
#     for record in challenge_records:
#         challenge_type_key = record.name
#         if challenge_type_key in challenges_by_type:
#             athlete = record.athlete
#             challenges_by_type[challenge_type_key]['athletes'].append({
#                 'full_name': f'{athlete.first_name} {athlete.last_name}',
#                 'id': athlete.id
#             })
#
#     # Prepare the result list
#     result = [value for key, value in challenges_by_type.items()]
#
#     return JsonResponse(result, safe=False)

#
# from django.http import JsonResponse
# from django.db.models import Prefetch, F, Value, CharField
# from django.db.models.functions import Concat


# def get_challenges_summary(request): # 4
#     challenge_summary = (
#         ChallengeRecord.objects
#         .select_related('athlete')
#         .values('name', 'athlete__id', 'athlete__first_name', 'athlete__last_name')
#     )
#
#     # Prepare a dictionary to gather data
#     challenges_by_type = {}
#     for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
#         challenges_by_type[challenge_type[0]] = {
#             'name_to_display': challenge_type[1],
#             'athletes': []
#         }
#
#     # Fill in the dictionary with athlete data
#     for entry in challenge_summary:
#         challenge_type_key = entry['name']
#         if challenge_type_key in challenges_by_type:
#             athlete_full_name = f"{entry['athlete__first_name']} {entry['athlete__last_name']}"
#             challenges_by_type[challenge_type_key]['athletes'].append({
#                 'full_name': athlete_full_name,
#                 'id': entry['athlete__id']
#             })
#
#     # Convert the dictionary to a list for the response
#     result = [value for value in challenges_by_type.values()]
#
#     return JsonResponse(result, safe=False)


def rate_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)

    # Parse the JSON request body
    data = json.loads(request.body)
    athlete_id = data.get('athlete', None)

    # Get the athlete by the ID provided in the body
    athlete = User.objects.filter(id=athlete_id).first()
    if not athlete:
        return JsonResponse({'status': False, }, status=400)

    if not AthleteCoachRelation.objects.filter(athlete_id=athlete_id, coach=coach).exists():
        return JsonResponse({'error': 'Для того чтобы ставить рейтинг надо быть подписанным на Coach'}, status=400)

    relation = AthleteCoachRelation.objects.filter(athlete_id=athlete_id, coach=coach).get()

    rating = data.get('rating', None)
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return JsonResponse({'status': False, }, status=400)

    relation.rate = rating
    relation.save()

    # Return success response
    return JsonResponse(
        {'status': True, 'message': f'{athlete.username} successfully rated {coach.username}'})


# 7
def analytics_for_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)
    athlete_ids = AthleteCoachRelation.objects.filter(coach=coach).values_list('athlete_id', flat=True)

    # Find the athlete with the maximum distance
    max_distance_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .annotate(max_distance=Max('distance'))
        .order_by('-max_distance')
        .values('athlete_id', 'max_distance')
        .first()
    )

    max_sum_distance_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .values('athlete_id')
        .annotate(sum_distance=Sum('distance'))
        .order_by('-sum_distance')
        .values('athlete_id', 'sum_distance')
        .first()
    )

    # Find the athlete with the maximum average speed
    max_avg_speed_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .values('athlete_id')
        .annotate(avg_speed=Avg('speed'))
        .order_by('-avg_speed')
        .values('athlete_id', 'avg_speed')
        .first()
    )

    return JsonResponse(
        {'longest_run_user': max_distance_run['athlete_id'],
         'longest_run_value': max_distance_run['max_distance'],
         'total_run_user': max_sum_distance_run['athlete_id'],
         'total_run_value': max_sum_distance_run['sum_distance'],
         'speed_avg_user': max_avg_speed_run['athlete_id'],
         'speed_avg_value': max_avg_speed_run['avg_speed']
         }
    )

# 23
def analytics_for_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)
    athlete_ids = AthleteCoachRelation.objects.filter(coach=coach).values_list('athlete_id', flat=True)

    # Initialize variables to keep track of the maximum values and corresponding athlete IDs
    max_distance = 0
    max_distance_athlete = None

    max_sum_distance = 0
    max_sum_distance_athlete = None

    max_avg_speed = 0
    max_avg_speed_athlete = None

    # Iterate over each athlete ID and calculate the metrics
    for athlete_id in athlete_ids:
        runs = Run.objects.filter(athlete_id=athlete_id)

        # Calculate the maximum single run distance for this athlete
        athlete_max_distance = runs.aggregate(Max('distance'))['distance__max'] or 0

        # Calculate the sum of all run distances for this athlete
        athlete_sum_distance = runs.aggregate(Sum('distance'))['distance__sum'] or 0

        # Calculate the average speed for this athlete
        athlete_avg_speed = runs.aggregate(Avg('speed'))['speed__avg'] or 0

        # Update max distance if this athlete has a longer run
        if athlete_max_distance > max_distance:
            max_distance = athlete_max_distance
            max_distance_athlete = athlete_id

        # Update max sum distance if this athlete has a greater total run distance
        if athlete_sum_distance > max_sum_distance:
            max_sum_distance = athlete_sum_distance
            max_sum_distance_athlete = athlete_id

        # Update max average speed if this athlete has a higher average speed
        if athlete_avg_speed > max_avg_speed:
            max_avg_speed = athlete_avg_speed
            max_avg_speed_athlete = athlete_id

    return JsonResponse(
        {
            'longest_run_user': max_distance_athlete,
            'longest_run_value': max_distance,
            'total_run_user': max_sum_distance_athlete,
            'total_run_value': max_sum_distance,
            'speed_avg_user': max_avg_speed_athlete,
            'speed_avg_value': max_avg_speed,
        }
    )


def analytics_for_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)
    athlete_ids = list(AthleteCoachRelation.objects.filter(coach=coach).values_list('athlete_id', flat=True))

    # Initialize variables to keep track of the maximum values and corresponding athlete IDs
    max_distance = 0
    max_distance_athlete = None

    max_sum_distance = 0
    max_sum_distance_athlete = None

    max_avg_speed = 0
    max_avg_speed_athlete = None

    # Iterate over each athlete ID and calculate the metrics
    for athlete_id in athlete_ids:
        # Get all runs for this athlete
        runs = list(Run.objects.filter(athlete_id=athlete_id))

        # Calculate the maximum single run distance for this athlete
        athlete_max_distance = 0
        for run in runs:
            if run.distance > athlete_max_distance:
                athlete_max_distance = run.distance

        # Calculate the sum of all run distances for this athlete
        athlete_sum_distance = 0
        for run in runs:
            athlete_sum_distance += run.distance

        # Calculate the average speed for this athlete
        total_speed = 0
        count = 0
        for run in runs:
            total_speed += run.speed
            count += 1
        athlete_avg_speed = total_speed / count if count > 0 else 0

        # Update max distance if this athlete has a longer run
        if athlete_max_distance > max_distance:
            max_distance = athlete_max_distance
            max_distance_athlete = athlete_id

        # Update max sum distance if this athlete has a greater total run distance
        if athlete_sum_distance > max_sum_distance:
            max_sum_distance = athlete_sum_distance
            max_sum_distance_athlete = athlete_id

        # Update max average speed if this athlete has a higher average speed
        if athlete_avg_speed > max_avg_speed:
            max_avg_speed = athlete_avg_speed
            max_avg_speed_athlete = athlete_id

    return JsonResponse(
        {
            'longest_run_user': max_distance_athlete,
            'longest_run_value': max_distance,
            'total_run_user': max_sum_distance_athlete,
            'total_run_value': max_sum_distance,
            'speed_avg_user': max_avg_speed_athlete,
            'speed_avg_value': max_avg_speed,
        }
    )
