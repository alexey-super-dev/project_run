from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Autos, Run  # Ensure the Autos model is imported
from .serializers import RunSerializer


def get_autos(request):
    autos = Autos.objects.all()
    # Set safe=False to allow a non-dict object (list) to be serialized
    return JsonResponse([{'name': auto.name} for auto in autos], safe=False)


def get_autos_page(request):
    autos = Autos.objects.all()
    return HttpResponse([f'name is {auto.name}\n' for auto in autos])


class RunsViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.filter()
    serializer_class = RunSerializer

    @action(detail=True, methods=['post'], url_path='start')
    def start_run(self, request, pk=None):
        try:
            run = self.get_object()  # Получить объект Run по ID из URL
        except Run.DoesNotExist:
            return Response({'error': 'Run not found'}, status=status.HTTP_404_NOT_FOUND)
            # Ваш код для запуска run

        if run.status == 'in_progress':
            return Response({'status': 'already run'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'in_progress'  # Например, метод start() запускает ваш объект
        run.save()
        return Response({'status': 'run started'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='stop')
    def stop_run(self, request, pk=None):
        try:
            run = self.get_object()  # Получить объект Run по ID из URL
        except Run.DoesNotExist:
            return Response({'error': 'Run not found'}, status=status.HTTP_404_NOT_FOUND)

        if run.status != 'in_progress':
            return Response({'status': 'Run not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'finished'
        run.save()
        return Response({'status': 'run stopped'}, status=status.HTTP_200_OK)
