from rest_framework import viewsets, serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from apps.subjects.models.Curso import Curso

class CursoSerializer(serializers.ModelSerializer):
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    especialidad_nombre = serializers.CharField(source='especialidad.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    trimestres = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'nivel', 'nivel_display', 'especialidad', 
                 'especialidad_nombre', 'periodo', 'periodo_nombre', 'trimestres']
        
    def validate(self, data):
        # Validar que el período académico esté activo
        if not data.get('periodo').activo:
            raise ValidationError(_('El período académico debe estar activo.'))
        
        # Validar que no exista otro curso con el mismo nivel y especialidad en el mismo periodo
        existing_curso = Curso.objects.filter(
            nivel=data.get('nivel'),
            especialidad=data.get('especialidad'),
            periodo=data.get('periodo')
        )
        
        if self.instance:
            existing_curso = existing_curso.exclude(pk=self.instance.pk)
            
        if existing_curso.exists():
            raise ValidationError(_('Ya existe un curso con el mismo nivel y especialidad para este período.'))
            
        return data
    
    def validate_nombre(self, value):
        if len(value.strip()) < 3:
            raise ValidationError(_('El nombre del curso debe tener al menos 3 caracteres.'))
        return value.strip()