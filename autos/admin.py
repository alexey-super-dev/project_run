from django.contrib import admin

from autos.models import Autos, Position, Run, CollectableItem

admin.site.register(Autos)
admin.site.register(Run)
admin.site.register(Position)
admin.site.register(CollectableItem)
