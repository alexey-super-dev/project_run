from django.http import JsonResponse

from autos.models import Autos


def get_autos(request):
    autos = Autos.objects.all()
    return JsonResponse([{'name': auto.name} for auto in autos])
