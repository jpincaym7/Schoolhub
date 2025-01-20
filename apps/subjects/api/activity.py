from rest_framework import serializers, viewsets, status
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from apps.students.models import Student
from apps.students.serializer import StudentSerializer
from apps.subjects.models import ActivityTemplate, Activity
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)

class ActivityTemplateSerializer(serializers.ModelSerializer):
    student_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Student.objects.all()),
        write_only=True,
        required=True
    )
    activities_count = serializers.SerializerMethodField()

    class Meta:
        model = ActivityTemplate
        fields = [
            'id', 'name', 'description', 'activity_type',
            'partial_number', 'subject', 'academic_period',
            'activities_count', 'student_ids'
        ]
        read_only_fields = ["sequence_number"]

    def get_activities_count(self, obj):
        return obj.activities.count()

    def validate(self, attrs):
        instance = ActivityTemplate(**{
            k: v for k, v in attrs.items() 
            if k != 'student_ids'
        })
        try:
            instance.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs

    def create(self, validated_data):
        student_ids = validated_data.pop('student_ids')
        
        try:
            with transaction.atomic():
                # Create the template first
                template = ActivityTemplate.objects.create(**validated_data)
                
                # Create activities for all students
                activities = template.create_activities_for_students(student_ids)
                
                return template
        except Exception as e:
            raise serializers.ValidationError(str(e))

class ActivitySerializer(serializers.ModelSerializer):
    student_details = serializers.SerializerMethodField(read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    template = serializers.PrimaryKeyRelatedField(
        queryset=ActivityTemplate.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Activity
        fields = [
            'id', 'name', 'description', 'activity_type',
            'partial_number', 'sequence_number', 'score',
            'subject', 'student', 'student_details', 'academic_period',
            'created_at', 'updated_at', 'template'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Añadir información sobre otras actividades relacionadas
        if instance.template:
            data['related_activities_count'] = instance.template.activities.count()
        return data

    def get_student_details(self, obj):
        try:
            if not obj or not hasattr(obj, 'student') or not obj.student:
                return None

            if isinstance(obj.student, str) and obj.student.isdigit():
                try:
                    student = Student.objects.get(id=int(obj.student))
                except Student.DoesNotExist:
                    return {'error': f'Student not found with ID: {obj.student}'}
            elif isinstance(obj.student, int):
                try:
                    student = Student.objects.get(id=obj.student)
                except Student.DoesNotExist:
                    return {'error': f'Student not found with ID: {obj.student}'}
            elif isinstance(obj.student, Student):
                student = obj.student
            else:
                return {'error': f'Invalid student data type: {type(obj.student)}'}

            parallel_data = None
            if hasattr(student, 'parallel'):
                if isinstance(student.parallel, str):
                    parallel_data = {
                        'id': None,
                        'name': student.parallel
                    }
                elif student.parallel and hasattr(student.parallel, 'id'):
                    parallel_data = {
                        'id': student.parallel.id,
                        'name': student.parallel.name
                    }

            student_data = {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'full_name': f"{student.last_name}, {student.first_name}",
                'photo': student.photo.url if hasattr(student, 'photo') and student.photo else None,
                'parallel': parallel_data,
                'is_active': student.is_active if hasattr(student, 'is_active') else None
            }
            return student_data

        except Exception as e:
            logger.exception("Error in get_student_details")
            return {'error': f'Error processing student details: {str(e)}'}

    def validate(self, data):
        """Validación adicional para asegurar consistencia con la plantilla"""
        template = data.get('template')
        if template:
            # Asegurar que los datos coincidan con la plantilla
            for field in ['name', 'description', 'activity_type', 'partial_number', 'subject', 'academic_period']:
                if field in data and getattr(template, field) != data[field]:
                    data[field] = getattr(template, field)
        return data

    def create(self, validated_data):
        """Method to create an activity with template validation"""
        template = validated_data.get('template')
        if template:
            # Asegurar que los datos coincidan con la plantilla
            for field in ['name', 'description', 'activity_type', 'partial_number', 'subject', 'academic_period']:
                validated_data[field] = getattr(template, field)
        
        activity = Activity(**validated_data)
        activity.clean()
        return super().create(validated_data)

class BulkActivityCreateSerializer(serializers.Serializer):
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=ActivityTemplate.objects.all()
    )
    student_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    )

    def create(self, validated_data):
        template = validated_data['template_id']
        students = validated_data['student_ids']
        
        with transaction.atomic():
            activities = Activity.bulk_create_from_template(template, students)
            return activities

class BulkScoreUpdateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    score = serializers.DecimalField(max_digits=4, decimal_places=2)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=ActivityTemplate.objects.all(),
        required=True
    )

    def validate_score(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError(
                _("La calificación debe estar entre 0 y 10")
            )
        return value