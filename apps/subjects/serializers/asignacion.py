from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.grades import AsignacionProfesor

class AsignacionProfesorSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.CharField(source='profesor.nombre', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)

    class Meta:
        model = AsignacionProfesor
        fields = [
            'id', 
            'profesor', 
            'profesor_nombre',
            'materia', 
            'materia_nombre',
            'curso', 
            'curso_nombre',
            'periodo', 
            'periodo_nombre'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """
        Validate that the assignment is unique and make any additional validations
        """
        # Check if professor already has this subject assigned in the same course and period
        if self.instance is None:  # Only for creation
            existing = AsignacionProfesor.objects.filter(
                profesor=data['profesor'],
                materia=data['materia'],
                curso=data['curso'],
                periodo=data['periodo']
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    _("Esta asignación ya existe para este profesor en el período seleccionado.")
                )

        return data