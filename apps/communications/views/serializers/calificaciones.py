from rest_framework import serializers
from apps.subjects.models.activity import PromedioTrimestre, PromedioAnual, Calificacion

class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = ['parcial', 'tarea1', 'tarea2', 'tarea3', 'tarea4', 'examen', 'promedio_final']

class PromedioTrimestreSerializer(serializers.ModelSerializer):
    estado = serializers.SerializerMethodField()
    
    class Meta:
        model = PromedioTrimestre
        fields = [
            'trimestre',
            'promedio_p1',
            'promedio_p2',
            'examen_trimestral',
            'proyecto_trimestral',
            'promedio_final',
            'estado'
        ]
    
    def get_estado(self, obj):
        if not obj.is_trimestre_completo():
            return "En Progreso"
        if obj.promedio_final >= 7:
            return "Aprobado"
        return "No Aprobado"

class PromedioAnualSerializer(serializers.ModelSerializer):
    estado_final = serializers.SerializerMethodField()
    materia = serializers.SerializerMethodField()
    
    class Meta:
        model = PromedioAnual
        fields = [
            'materia',
            'promedio_t1',
            'promedio_t2',
            'promedio_t3',
            'promedio_final',
            'estado_final'
        ]
    
    def get_estado_final(self, obj):
        if obj.promedio_t1 == 0 or obj.promedio_t2 == 0 or obj.promedio_t3 == 0:
            return "En Progreso"
        if obj.promedio_final >= 7:
            return "Aprobado"
        return "No Aprobado"
    
    def get_materia(self, obj):
        return obj.detalle_matricula.materia.nombre