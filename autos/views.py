from django.http import HttpResponse


def get_autos(request):
    return HttpResponse({'ok': "Hello World"})
