from rest_framework import serializers

from autos.models import Run


class RunSerializer(serializers.ModelSerializer):
    comment2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Run
        fields = ['id', 'runner', 'comment', 'comment2']
