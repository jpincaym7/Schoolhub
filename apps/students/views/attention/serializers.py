from rest_framework import serializers, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from datetime import date
from apps.students.models import Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'date', 'status',
            'status_display', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'student': {'write_only': True},
            'status': {'required': True}
        }

    def validate(self, data):
        """
        Realizar validaciones personalizadas de los datos
        """
        # Validar fecha futura
        if data.get('date') > date.today():
            raise serializers.ValidationError({
                'date': _('No se puede registrar asistencia para fechas futuras.')
            })

        # Validar registro duplicado en creación
        if not self.instance:
            existing = Attendance.objects.filter(
                student=data['student'],
                date=data['date']
            ).exists()
            if existing:
                raise serializers.ValidationError({
                    'student': _('Ya existe un registro de asistencia para este estudiante en esta fecha.')
                })

        # Validar justificación dentro de 3 días
        if data.get('status') == 'justified':
            days_difference = date.today() - data['date']
            if days_difference.days > 3:
                raise serializers.ValidationError({
                    'status': _('No se puede justificar una asistencia después de 3 días.')
                })

        return data

    def to_representation(self, instance):
        """
        Personalizar la representación de la respuesta
        """
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")
        data['updated_at'] = instance.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        return data


class AttendanceBulkSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    date = serializers.DateField(required=True)
    status = serializers.ChoiceField(
        choices=['present', 'absent', 'late', 'justified'],
        required=True
    )
    comments = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """
        Realizar validaciones personalizadas para el registro masivo
        """
        today = date.today()
        
        # Validar fecha futura
        if data['date'] > today:
            raise serializers.ValidationError({
                'date': _('No se puede registrar asistencia para fechas futuras.')
            })

        # Si es justificación, validar que sea dentro de los últimos 3 días
        if data['status'] == 'justified':
            days_difference = today - data['date']
            if days_difference.days > 3:
                raise serializers.ValidationError({
                    'status': _('No se puede justificar una asistencia después de 3 días.')
                })

        # Filtrar estudiantes que ya tienen asistencia registrada
        existing_attendances = Attendance.objects.filter(
            student_id__in=data['student_ids'],
            date=data['date']
        ).values_list('student_id', flat=True)

        if existing_attendances:
            # Si es justificación, permitir solo para estudiantes sin asistencia registrada
            if data['status'] == 'justified':
                # Filtrar los IDs de estudiantes, dejando solo los que no tienen asistencia
                data['student_ids'] = [
                    student_id for student_id in data['student_ids']
                    if student_id not in existing_attendances
                ]
                
                # Si no quedan estudiantes para justificar
                if not data['student_ids']:
                    raise serializers.ValidationError({
                        'student_ids': _('No hay estudiantes sin asistencia registrada para justificar en esta fecha.')
                    })
            else:
                # Para otros estados, mostrar error con los estudiantes que ya tienen registro
                raise serializers.ValidationError({
                    'student_ids': _(
                        'Los siguientes estudiantes ya tienen registro de asistencia para esta fecha: {}'
                    ).format(list(existing_attendances))
                })

        return data