from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date
from apps.students.models import Behavior, BehaviorSummary
from apps.subjects.models import AcademicPeriod

class AcademicPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['id', 'number', 'school_year']

class BehaviorSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Behavior
        fields = [
            'id', 'student', 'student_name', 'date', 'type', 'type_display',
            'description', 'reported_by', 'reported_by_name', 'academic_period',
            'partial_number'
        ]
        read_only_fields = ['reported_by']

    def validate_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                _('No se puede registrar comportamiento para fechas futuras.')
            )
        return value

    def validate_partial_number(self, value):
        if not (1 <= value <= 3):
            raise serializers.ValidationError(
                _('El número de parcial debe estar entre 1 y 3.')
            )
        return value

    def create(self, validated_data):
        # Asignar automáticamente el usuario que reporta
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)

class BehaviorSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    partial_summaries = serializers.SerializerMethodField()

    class Meta:
        model = BehaviorSummary
        fields = [
            'id', 'student', 'student_name', 'academic_period',
            'positive_count', 'negative_count', 'neutral_count',
            'updated_at', 'partial_summaries'
        ]
        read_only_fields = [
            'positive_count', 'negative_count', 'neutral_count',
            'updated_at', 'partial_summaries'
        ]

    def get_partial_summaries(self, obj):
        return {
            f'partial_{i}': obj.get_partial_counts(i)
            for i in range(1, 4)
        }