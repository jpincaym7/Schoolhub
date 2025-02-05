import logging
from rest_framework import serializers, viewsets, status
from django.db import transaction

from apps.students.models import DetalleMatricula, DetalleMatriculaTrimestre, Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.activity import Calificacion, PromedioAnual, PromedioTrimestre
from apps.subjects.models.subject import Materia

logger = logging.getLogger(__name__)

class DetalleMatriculaTrimestreSerializer(serializers.ModelSerializer):
    trimestre_nombre = serializers.CharField(source='trimestre.get_trimestre_display', read_only=True)
    
    class Meta:
        model = DetalleMatriculaTrimestre
        fields = ['id', 'trimestre', 'trimestre_nombre']
        read_only_fields = ['id']

class DetalleMatriculaSerializer(serializers.ModelSerializer):
    nombre_materia = serializers.CharField(source='materia.nombre', read_only=True)
    codigo_materia = serializers.CharField(source='materia.codigo', read_only=True)
    creditos = serializers.IntegerField(source='materia.creditos', read_only=True)
    detalles_trimestre = DetalleMatriculaTrimestreSerializer(many=True, read_only=True)

    class Meta:
        model = DetalleMatricula
        fields = ['id', 'materia', 'nombre_materia', 'codigo_materia', 
                 'creditos', 'fecha_agregada', 'detalles_trimestre']
        read_only_fields = ['fecha_agregada', 'detalles_trimestre']
               
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
        estudiante = data.get('estudiante')
        periodo = data.get('periodo')
        materias_ids = data.get('materias_ids', [])

        # Validate student course assignment
        if not estudiante.curso:
            raise serializers.ValidationError(
                "El estudiante debe tener un curso asignado para poder matricularse."
            )

        # Validate course trimesters
        if not estudiante.curso.trimestres.exists():
            raise serializers.ValidationError(
                "El curso del estudiante debe tener trimestres asignados."
            )
        
        # Validate existing enrollment
        existing_matricula = Matricula.objects.filter(
            estudiante=estudiante,
            periodo=periodo
        )
        
        if self.instance is None and existing_matricula.exists():
            raise serializers.ValidationError(
                "El estudiante ya tiene una matrícula en este período."
            )

        # Validate subjects if provided
        if materias_ids:
            # Validate subject existence
            materias = Materia.objects.filter(id__in=materias_ids)
            if len(materias) != len(materias_ids):
                raise serializers.ValidationError(
                    "Una o más materias seleccionadas no existen."
                )
            
            # Validate duplicate enrollment
            if not self.instance:  # Only check for new enrollments
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
            
            # Validate removal of subjects with grades (only for updates)
            if self.instance:
                current_subjects = set(self.instance.detallematricula_set.values_list('materia_id', flat=True))
                new_subjects = set(materias_ids)
                subjects_to_remove = current_subjects - new_subjects
                
                if subjects_to_remove:
                    subjects_with_grades = DetalleMatricula.objects.filter(
                        matricula=self.instance,
                        materia_id__in=subjects_to_remove,
                        calificacion__isnull=False
                    ).distinct().values_list('materia__nombre', flat=True)
                    
                    if subjects_with_grades:
                        raise serializers.ValidationError(
                            f"No se pueden eliminar las siguientes materias porque tienen calificaciones registradas: {', '.join(subjects_with_grades)}"
                        )

        return data

    @transaction.atomic
    def create(self, validated_data):
        materias_ids = validated_data.pop('materias_ids', [])
        
        matricula = Matricula.objects.create(**validated_data)
        matricula.numero_matricula = f"M_IC{matricula.id:06d}"
        matricula.save()

        for materia_id in materias_ids:
            DetalleMatricula.objects.create(
                matricula=matricula,
                materia_id=materia_id
            )

        return matricula

    def update(self, instance, validated_data):
        materias_ids = validated_data.pop('materias_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if materias_ids is not None:
            detalles_actuales = instance.detallematricula_set.all()
            materias_actuales = set(detalles_actuales.values_list('materia_id', flat=True))
            materias_nuevas = set(materias_ids)
            
            # Add new subjects
            for materia_id in materias_nuevas - materias_actuales:
                DetalleMatricula.objects.create(
                    matricula=instance,
                    materia_id=materia_id
                )
            
            # Remove subjects (validation already done in validate method)
            materias_removidas = materias_actuales - materias_nuevas
            instance.detallematricula_set.filter(materia_id__in=materias_removidas).delete()

        return instance