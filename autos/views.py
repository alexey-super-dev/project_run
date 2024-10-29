import json

from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
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

from .logic import calculate_run_time_by_id, calculate_run_time, calculate_run_time_different_way, calculate_median
from .models import Autos, Run, Position, AthleteCoachRelation  # Ensure the Autos model is imported
from .serializers import RunSerializer, PositionSerializer, UserSerializer, DetailAthleteSerializer, \
    DetailCoachSerializer


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
            run.speed = round(calculate_median(list(Position.objects.filter(run=run).values_list('speed', flat=True))), 2)
            # run.run_time_seconds = calculate_run_time_by_id(run)
            run.run_time_seconds = calculate_run_time_different_way(run)
        run.save()

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
            previous_position = Position.objects.filter(run_id=position.run_id, date_time__lt=date_time).latest('date_time')
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
        # Check if this is a detail request by looking at the URL kwargs
        if self.action == 'retrieve':
            # Retrieve the user instance to be serialized
            user = self.get_object()
            # Choose the serializer based on the user's `is_staff` flag
            if user.is_staff:
                return DetailCoachSerializer
            return DetailAthleteSerializer
        # Default serializer for list view
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Exclude superusers from the queryset
        queryset = queryset.filter(is_superuser=False)

        # Get the 'type' query parameter
        user_type = self.request.query_params.get('type', None)

        # Filter based on 'type' query parameter
        if user_type == 'coach':
            queryset = queryset.filter(is_staff=True)
        elif user_type == 'athlete':
            queryset = queryset.filter(is_staff=False)

        return queryset
        # return queryset.annotate(
        #     runs_finished_count=Count('run', filter=Q(run__status='finished'))
        # )


