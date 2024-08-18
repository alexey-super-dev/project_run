from rest_framework import serializers

from autos.models import Run


class RunSerializer(serializers.ModelSerializer):

    class Meta:
        model = Run
        fields = ['id', 'runner', 'comment']
