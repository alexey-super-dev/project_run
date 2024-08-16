from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Autos, Run  # Ensure the Autos model is imported
from .serializers import RunSerializer


def get_autos(request):
    autos = Autos.objects.all()
    # Set safe=False to allow a non-dict object (list) to be serialized
    return JsonResponse([{'name': auto.name} for auto in autos], safe=False)


def get_autos_page(request):
    autos = Autos.objects.all()
    return HttpResponse([f'name is {auto.name}\n' for auto in autos])


class RunsViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer

    def list(self, request, *args, **kwargs):
        a = b
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
