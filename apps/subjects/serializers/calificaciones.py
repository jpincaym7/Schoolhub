from rest_framework import serializers
from apps.subjects.models.activity import Calificacion, PromedioAnual

class CalificacionSerializer(serializers.ModelSerializer):
    # Agregar el nombre del estudiante
    estudiante = serializers.CharField(source='detalle_matricula.matricula.estudiante.usuario.get_full_name', read_only=True)
    
    # Agregar el nombre del profesor
    profesor = serializers.CharField(source='asignacion_profesor.profesor.usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Calificacion
        fields = [
            'id', 'detalle_matricula', 'asignacion_profesor', 'parcial',
            'tarea1', 'tarea2', 'tarea3', 'tarea4', 'examen', 'promedio_final',
            'fecha_registro', 'fecha_actualizacion', 'estudiante', 'profesor'
        ]
        read_only_fields = ['promedio_final', 'fecha_registro', 'fecha_actualizacion']

    def validate(self, data):
        if data['detalle_matricula'].materia != data['asignacion_profesor'].materia:
            raise serializers.ValidationError("La materia de la matrícula no coincide con la materia asignada al profesor")
        if data['detalle_matricula'].matricula.periodo != data['asignacion_profesor'].periodo:
            raise serializers.ValidationError("Los períodos académicos no coinciden")
        return data

class PromedioAnualSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromedioAnual
        fields = ['id', 'detalle_matricula', 'promedio_p1', 'promedio_p2', 'promedio_final']
        read_only_fields = ['promedio_final']