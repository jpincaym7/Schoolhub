import logging
from rest_framework import serializers, viewsets, status
from django.db import transaction
from apps.students.models import Matricula, DetalleMatricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia
from apps.students.models import Estudiante

logger = logging.getLogger(__name__)

class DetalleMatriculaSerializer(serializers.ModelSerializer):
    nombre_materia = serializers.CharField(source='materia.nombre', read_only=True)
    codigo_materia = serializers.CharField(source='materia.codigo', read_only=True)
    creditos = serializers.IntegerField(source='materia.creditos', read_only=True)

    class Meta:
        model = DetalleMatricula
        fields = ['id', 'materia', 'nombre_materia', 'codigo_materia', 'creditos', 'fecha_agregada']
        read_only_fields = ['fecha_agregada']
               
class MatriculaSerializer(serializers.ModelSerializer):
    detalles = DetalleMatriculaSerializer(
        source='detallematricula_set',
        many=True,
        read_only=True
    )
    materias_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    periodo_nombre = serializers.CharField(
        source='periodo.nombre',
        read_only=True
    )
    estudiante_get_full_name = serializers.CharField(
        source='estudiante.__str__',
        read_only=True
    )
    materias = serializers.SerializerMethodField()
    
    estudiante = serializers.PrimaryKeyRelatedField(
        queryset=Estudiante.objects.all(),
    )
    periodo = serializers.PrimaryKeyRelatedField(
        queryset=PeriodoAcademico.objects.all(),
    )

    class Meta:
        model = Matricula
        fields = ['id', 'estudiante', 'estudiante_get_full_name', 'periodo',
                 'periodo_nombre', 'numero_matricula', 'fecha_inscripcion',
                 'detalles', 'materias_ids', 'materias']
        read_only_fields = ['numero_matricula', 'fecha_inscripcion']

    def get_materias(self, obj):
        return [materia.nombre for materia in obj.materias.all()]

    def validate(self, data):
        """
        Valida que:
        1. El estudiante pueda inscribirse en el período dado
        2. Las materias seleccionadas no estén ya matriculadas
        3. Evita duplicación de matrículas
        """
        estudiante = data.get('estudiante')
        periodo = data.get('periodo')
        materias_ids = data.get('materias_ids', [])
        
        # Verificar si ya existe una matrícula en este período
        existing_matricula = Matricula.objects.filter(
            estudiante=estudiante,
            periodo=periodo
        )
        
        # Para creación de nueva matrícula
        if self.instance is None:
            if existing_matricula.exists():
                raise serializers.ValidationError(
                    "El estudiante ya tiene una matrícula en este período."
                )
        
        # Validar materias
        if materias_ids:
            # Verificar existencia de materias
            materias = Materia.objects.filter(id__in=materias_ids)
            if len(materias) != len(materias_ids):
                raise serializers.ValidationError(
                    "Una o más materias seleccionadas no existen."
                )
            
            # Verificar materias ya matriculadas en este período
            already_enrolled = DetalleMatricula.objects.filter(
                matricula__estudiante=estudiante,
                matricula__periodo=periodo,
                materia_id__in=materias_ids
            )
            
            if already_enrolled.exists():
                enrolled_subject_names = list(already_enrolled.values_list('materia__nombre', flat=True))
                raise serializers.ValidationError(
                    f"Ya estás matriculado en las siguientes materias: {', '.join(enrolled_subject_names)}"
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        materias_ids = validated_data.pop('materias_ids', [])
        
        # Verificar si ya existe una matrícula (evitar duplicación)
        existing_matricula = Matricula.objects.filter(
            estudiante=validated_data['estudiante'],
            periodo=validated_data['periodo']
        ).first()
        
        if existing_matricula:
            # Actualizar matrícula existente en lugar de crear nueva
            matricula = existing_matricula
            
            # Actualizar detalles de materias
            # Primero eliminar materias existentes que no están en la nueva lista
            existing_details = matricula.detallematricula_set
            existing_details.exclude(materia_id__in=materias_ids).delete()
            
            # Añadir nuevas materias que no existen
            existing_materia_ids = set(existing_details.values_list('materia_id', flat=True))
            for materia_id in materias_ids:
                if materia_id not in existing_materia_ids:
                    DetalleMatricula.objects.create(
                        matricula=matricula,
                        materia_id=materia_id
                    )
        else:
            # Crear nueva matrícula si no existe
            matricula = Matricula.objects.create(**validated_data)
            
            # Generar número de matrícula
            matricula.numero_matricula = f"M{matricula.id:06d}"
            matricula.save()

            # Crear detalles de matrícula
            for materia_id in materias_ids:
                DetalleMatricula.objects.create(
                    matricula=matricula,
                    materia_id=materia_id
                )

        return matricula

    def update(self, instance, validated_data):
        # Método de actualización similar a la lógica de creación
        materias_ids = validated_data.pop('materias_ids', None)
        
        # Actualizar los datos principales de la matrícula
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar las materias si se proporcionaron
        if materias_ids is not None:
            # Eliminar materias existentes no incluidas en la nueva lista
            instance.detallematricula_set.exclude(
                materia_id__in=materias_ids
            ).delete()

            # Agregar nuevas materias
            existing_materias = set(
                instance.detallematricula_set.values_list('materia_id', flat=True)
            )
            for materia_id in materias_ids:
                if materia_id not in existing_materias:
                    DetalleMatricula.objects.create(
                        matricula=instance,
                        materia_id=materia_id
                    )

        return instance