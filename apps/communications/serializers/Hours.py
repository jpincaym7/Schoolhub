from rest_framework import serializers
from apps.subjects.models import Subject
from apps.subjects.serializers import SubjectSerializer
from apps.communications.models import TeacherOfficeHours
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class TeacherOfficeHoursSerializer(serializers.ModelSerializer):
    """
    Serializer for managing teacher office hours
    """
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    formatted_schedule = serializers.SerializerMethodField()

    class Meta:
        model = TeacherOfficeHours
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'day_of_week',
            'day_of_week_display',
            'start_time',
            'end_time',
            'location',
            'description',
            'is_active',
            'formatted_schedule',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_formatted_schedule(self, obj):
        """
        Returns a formatted representation of the schedule
        """
        return f"{obj.get_day_of_week_display()}: {obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"

    def validate(self, data):
        """
        Custom validations for office hours
        """
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        teacher = data.get('teacher')
        day_of_week = data.get('day_of_week')

        # Validate end time is after start time
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': _('La hora de fin debe ser posterior a la hora de inicio')
            })

        # Verify schedule overlap for the same teacher
        if teacher and day_of_week is not None:
            overlapping_hours = TeacherOfficeHours.objects.filter(
                teacher=teacher,
                day_of_week=day_of_week,
                is_active=True
            )

            # Exclude current instance in case of update
            instance = self.instance
            if instance:
                overlapping_hours = overlapping_hours.exclude(pk=instance.pk)

            for hours in overlapping_hours:
                if (start_time <= hours.end_time and end_time >= hours.start_time):
                    raise serializers.ValidationError(
                        _('Este horario se solapa con otro horario de atención existente')
                    )

        return data

    def to_representation(self, instance):
        """
        Customizes the serialized instance representation
        """
        data = super().to_representation(instance)
        
        # Format creation and update dates
        data['created_at'] = timezone.localtime(instance.created_at).strftime("%d/%m/%Y %H:%M")
        data['updated_at'] = timezone.localtime(instance.updated_at).strftime("%d/%m/%Y %H:%M")

        return data

class TeacherOfficeHoursListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for office hours listings
    """
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    schedule = serializers.SerializerMethodField()

    class Meta:
        model = TeacherOfficeHours
        fields = [
            'id',
            'teacher_name',
            'schedule',
            'start_time',
            'end_time',
            'location',
            'description',
            'is_active'
        ]

    def get_schedule(self, obj):
        return f"{obj.get_day_of_week_display()}: {obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"