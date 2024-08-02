from django.http import HttpResponse, JsonResponse


def get_autos(request):
    return JsonResponse({'ok': "Hello World"})
