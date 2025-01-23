from rest_framework import serializers
from apps.students.models import Estudiante
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia
from apps.users.models import User 

class EstudianteSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()  # Muestra el nombre completo del usuario (usando __str__ de User)
    curso = serializers.StringRelatedField()  # Muestra el nombre del curso (suponiendo que tiene un campo __str__)

    class Meta:
        model = Estudiante
        fields = ['id', 'usuario', 'curso']
        
class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'activo']

class MateriaSerializer(serializers.ModelSerializer):
    especialidad = serializers.StringRelatedField()  # Muestra el nombre o representación de la especialidad

    class Meta:
        model = Materia
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'horas_semanales', 'especialidad']