from rest_framework import serializers
from apps.students.models import Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia
from apps.users.models import User 

class EstudianteSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()
    curso = serializers.StringRelatedField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Estudiante
        fields = ['id', 'usuario', 'curso', 'is_enrolled']
    
    def get_is_enrolled(self, obj):
        """
        Check if the student is already enrolled in the current active period
        """
        current_period = PeriodoAcademico.objects.filter(activo=True).first()
        if not current_period:
            return False
        
        return Matricula.objects.filter(
            estudiante=obj, 
            periodo=current_period
        ).exists()
        
class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'activo']

class MateriaSerializer(serializers.ModelSerializer):
    especialidad = serializers.StringRelatedField()  # Muestra el nombre o representación de la especialidad

    class Meta:
        model = Materia
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'horas_semanales', 'especialidad']