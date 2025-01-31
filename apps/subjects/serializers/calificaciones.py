from rest_framework import serializers
from apps.subjects.models.activity import (
    Calificacion, PromedioAnual, PromedioTrimestre, 
    Trimestre, Parcial
)

class TrimestreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trimestre
        fields = ['id', 'periodo', 'trimestre']

class ParcialSerializer(serializers.ModelSerializer):
    trimestre_nombre = serializers.CharField(source='trimestre.get_trimestre_display', read_only=True)
    
    class Meta:
        model = Parcial
        fields = ['id', 'trimestre', 'numero', 'trimestre_nombre']

class CalificacionSerializer(serializers.ModelSerializer):
    # Información del estudiante
    estudiante = serializers.CharField(
        source='detalle_matricula.matricula.estudiante.usuario.get_full_name', 
        read_only=True
    )
    
    # Información del profesor
    profesor = serializers.CharField(
        source='asignacion_profesor.profesor.usuario.get_full_name', 
        read_only=True
    )
    
    # Información del parcial y trimestre
    parcial_numero = serializers.IntegerField(source='parcial.numero', read_only=True)
    trimestre_nombre = serializers.CharField(
        source='parcial.trimestre.get_trimestre_display', 
        read_only=True
    )
    
    class Meta:
        model = Calificacion
        fields = [
            'id', 
            'detalle_matricula', 
            'asignacion_profesor', 
            'parcial',
            'parcial_numero',
            'trimestre_nombre',
            'tarea1', 
            'tarea2', 
            'tarea3', 
            'tarea4', 
            'examen', 
            'promedio_final',
            'fecha_registro', 
            'fecha_actualizacion', 
            'estudiante', 
            'profesor'
        ]
        read_only_fields = [
            'promedio_final', 
            'fecha_registro', 
            'fecha_actualizacion',
            'parcial_numero',
            'trimestre_nombre'
        ]

    def validate(self, data):
        # Validar que la materia coincida
        if data['detalle_matricula'].materia != data['asignacion_profesor'].materia:
            raise serializers.ValidationError(
                "La materia de la matrícula no coincide con la materia asignada al profesor"
            )
        
        # Validar que el período coincida
        if data['detalle_matricula'].matricula.periodo != data['asignacion_profesor'].periodo:
            raise serializers.ValidationError(
                "Los períodos académicos no coinciden"
            )
        
        # Validar que el trimestre corresponda al período académico
        if data['parcial'].trimestre.periodo != data['detalle_matricula'].matricula.periodo:
            raise serializers.ValidationError(
                "El trimestre no corresponde al período académico del estudiante"
            )
        
        return data

class PromedioTrimestreSerializer(serializers.ModelSerializer):
    trimestre_nombre = serializers.CharField(source='trimestre.get_trimestre_display', read_only=True)
    estudiante = serializers.CharField(
        source='detalle_matricula.matricula.estudiante.usuario.get_full_name', 
        read_only=True
    )
    materia = serializers.CharField(source='detalle_matricula.materia.nombre', read_only=True)
    
    class Meta:
        model = PromedioTrimestre
        fields = [
            'id', 
            'detalle_matricula', 
            'trimestre',
            'trimestre_nombre',
            'promedio_p1', 
            'promedio_p2', 
            'examen_trimestral',
            'promedio_final',
            'estudiante',
            'materia'
        ]
        read_only_fields = [
            'promedio_final',
            'promedio_p1',
            'promedio_p2'
        ]

class PromedioAnualSerializer(serializers.ModelSerializer):
    estudiante = serializers.CharField(
        source='detalle_matricula.matricula.estudiante.usuario.get_full_name', 
        read_only=True
    )
    materia = serializers.CharField(source='detalle_matricula.materia.nombre', read_only=True)
    
    class Meta:
        model = PromedioAnual
        fields = [
            'id', 
            'detalle_matricula', 
            'promedio_t1', 
            'promedio_t2', 
            'promedio_t3',
            'promedio_final',
            'estudiante',
            'materia'
        ]
        read_only_fields = [
            'promedio_final',
            'promedio_t1',
            'promedio_t2',
            'promedio_t3'
        ]

class CalificacionDetalleSerializer(CalificacionSerializer):
    """Serializer extendido para mostrar más detalles en vistas específicas"""
    materia = serializers.CharField(source='detalle_matricula.materia.nombre', read_only=True)
    curso = serializers.CharField(
        source='detalle_matricula.matricula.estudiante.curso.nombre', 
        read_only=True
    )
    periodo = serializers.CharField(
        source='detalle_matricula.matricula.periodo.nombre',
        read_only=True
    )
    
    class Meta(CalificacionSerializer.Meta):
        fields = CalificacionSerializer.Meta.fields + ['materia', 'curso', 'periodo']