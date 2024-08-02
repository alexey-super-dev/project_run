from django.http import JsonResponse
from .models import Autos  # Ensure the Autos model is imported

def get_autos(request):
    autos = Autos.objects.all()
    # Set safe=False to allow a non-dict object (list) to be serialized
    return JsonResponse([{'name': auto.name} for auto in autos], safe=False)