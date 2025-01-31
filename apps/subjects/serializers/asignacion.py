from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.subjects.models.grades import AsignacionProfesor, AsignacionProfesorTrimestre

class AsignacionProfesorTrimestreSerializer(serializers.ModelSerializer):
    trimestre_nombre = serializers.CharField(source='trimestre.get_trimestre_display', read_only=True)
    
    class Meta:
        model = AsignacionProfesorTrimestre
        fields = ['id', 'trimestre', 'trimestre_nombre']
        read_only_fields = ['id']

class AsignacionProfesorSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.CharField(source='profesor.nombre', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='periodo.nombre', read_only=True)
    asignaciones_trimestre = AsignacionProfesorTrimestreSerializer(many=True, read_only=True)

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
            'periodo_nombre',
            'asignaciones_trimestre'
        ]
        read_only_fields = ['id', 'asignaciones_trimestre']

    def validate(self, data):
        """
        Validación completa de asignaciones de profesores
        """
        if self.instance is None:  # Solo para creación
            # Verificar si el profesor ya tiene esta asignación
            existing_same_professor = AsignacionProfesor.objects.filter(
                profesor=data['profesor'],
                materia=data['materia'],
                curso=data['curso'],
                periodo=data['periodo']
            ).exists()
            
            if existing_same_professor:
                raise serializers.ValidationError({
                    "error": "duplicate_assignment",
                    "detail": "Esta asignación ya existe para este profesor en el período seleccionado.",
                    "code": "duplicate_professor_assignment",
                    "profesor": str(data['profesor']),
                    "materia": str(data['materia']),
                    "curso": str(data['curso']),
                    "periodo": str(data['periodo'])
                })

            # Verificar si la materia ya está asignada a otro profesor
            existing_other_professor = AsignacionProfesor.objects.filter(
                materia=data['materia'],
                curso=data['curso'],
                periodo=data['periodo']
            ).exclude(profesor=data['profesor']).first()
            
            if existing_other_professor:
                raise serializers.ValidationError({
                    "error": "subject_already_assigned",
                    "detail": f"La materia ya está asignada al profesor {existing_other_professor.profesor} en este curso y periodo",
                    "code": "existing_assignment",
                    "current_teacher": str(existing_other_professor.profesor),
                    "subject": str(data['materia']),
                    "course": str(data['curso']),
                    "period": str(data['periodo'])
                })

            # Verificar que el curso tenga trimestres asignados
            if not data['curso'].trimestres.exists():
                raise serializers.ValidationError({
                    "error": "no_trimestres",
                    "detail": "El curso seleccionado no tiene trimestres asignados",
                    "code": "missing_trimestres"
                })

        return data

    def to_representation(self, instance):
        """
        Personalizar la representación de la respuesta
        """
        representation = super().to_representation(instance)
        return representation