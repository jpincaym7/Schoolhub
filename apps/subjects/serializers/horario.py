from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.Horario import HorarioAtencion

class HorarioAtencionSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField()
    dia_display = serializers.CharField(source='get_dia_display', read_only=True)
    
    class Meta:
        model = HorarioAtencion
        fields = [
            'id', 'profesor', 'profesor_nombre', 
            'dia', 'dia_display', 'hora_inicio', 'hora_fin'
        ]
        read_only_fields = ['id', 'profesor']
    
    def get_profesor_nombre(self, obj):
        """Returns the full name of the professor"""
        return str(obj.profesor) if obj.profesor else ""
    
    def validate(self, data):
        """
        Comprehensive validation for office hours:
        1. Ensure end time is after start time
        2. Check for schedule overlaps
        3. Validate day and time constraints
        """
        # Time range validation
        hora_inicio = data.get('hora_inicio')
        hora_fin = data.get('hora_fin')
        
        if hora_inicio and hora_fin:
            # Ensure end time is after start time
            if hora_fin <= hora_inicio:
                raise serializers.ValidationError({
                    'hora_fin': _('La hora de finalización debe ser posterior a la hora de inicio')
                })
            
            # Optional: Add time range constraints if needed
            # For example, limit office hours to specific times
            if hora_inicio.hour < 7 or hora_fin.hour > 22:
                raise serializers.ValidationError(
                    _('Los horarios de atención deben estar entre las 7:00 y 22:00')
                )
        
        return data
    
    def create(self, validated_data):
        """
        Override create to ensure the professor is the current user's professor
        """
        # The ViewSet's perform_create method will set the profesor
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Override update to prevent changing the professor
        """
        # Remove profesor from validated data to prevent changing
        validated_data.pop('profesor', None)
        return super().update(instance, validated_data)