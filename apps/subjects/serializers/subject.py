from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.subject import Materia

class ProfesorSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar el nombre completo del profesor.
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Profesor
        fields = ['nombre_completo']

    def get_nombre_completo(self, obj):
        """
        Devuelve el nombre completo del profesor (nombre + apellido).
        """
        return f"{obj.usuario.first_name} {obj.usuario.last_name}"

class MateriaSerializer(serializers.ModelSerializer):
    profesor = serializers.SerializerMethodField()  # Campo calculado para el profesor

    class Meta:
        model = Materia
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'horas_semanales', 'especialidad', 'profesor']
        extra_kwargs = {
            'codigo': {'validators': []},  # Opcional: Elimina validadores adicionales para evitar conflictos con la validación personalizada.
        }

    def get_profesor(self, obj):
        """
        Obtiene el nombre completo del profesor relacionado a la materia.
        """
        asignacion = AsignacionProfesor.objects.filter(materia=obj).first()
        if asignacion and asignacion.profesor:
            return ProfesorSerializer(asignacion.profesor).data['nombre_completo']
        return None

    def validate_codigo(self, value):
        """
        Valida que el código de la materia sea único (insensible a mayúsculas/minúsculas).
        """
        if Materia.objects.filter(codigo__iexact=value).exists():
            if self.instance and self.instance.codigo.lower() == value.lower():
                return value
            raise serializers.ValidationError("Ya existe una materia con este código.")
        return value
