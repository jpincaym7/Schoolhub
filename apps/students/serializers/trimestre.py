from rest_framework import serializers
from apps.subjects.models.academic import Trimestre

class TrimestreSerializer(serializers.ModelSerializer):
    # Opcional: puedes incluir el nombre del periodo en lugar del ID si lo prefieres
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)

    class Meta:
        model = Trimestre
        fields = ['id', 'periodo', 'trimestre', 'periodo_nombre']