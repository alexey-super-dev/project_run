from django.contrib import admin

from autos.models import Autos, Position, Run

admin.site.register(Autos)
admin.site.register(Run)
admin.site.register(Position)
