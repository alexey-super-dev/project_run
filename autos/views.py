from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets

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
    queryset = Run.objects.all()
    serializer_class = RunSerializer
