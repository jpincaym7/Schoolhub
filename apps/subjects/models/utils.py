from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from typing import Dict, List
from django.utils import timezone
from django.db.models import Max
from apps.subjects.models import (
    Activity,
    AcademicPeriod,
    Subject,
    PartialGrade,
    ActivityTemplate,
)

class ActivityCreator:
    @classmethod
    def create_from_template(cls, template, students) -> List['Activity']:
        """
        Creates activities for multiple students based on a template,
        handling sequence numbers and validating limits per activity type.
        """
        from apps.subjects.models import Activity  # Import here to avoid circular imports
        
        activities_to_create = []
        
        with transaction.atomic():
            for student in students:
                # Check if student has reached the limit for this activity type and partial
                existing_activities_count = Activity.objects.filter(
                    student=student,
                    subject=template.subject,
                    academic_period=template.academic_period,
                    partial_number=template.partial_number,
                    activity_type=template.activity_type
                ).count()
                
                # Validate activity type limits (max 2 per type per partial)
                if existing_activities_count >= 2:
                    raise ValidationError(
                        _('El estudiante %(student)s ya tiene el máximo de actividades %(type)s '
                          'permitidas (2) para el parcial %(partial)d.'),
                        params={
                            'student': student,
                            'type': template.get_activity_type_display(),
                            'partial': template.partial_number
                        }
                    )
                
                # Get the next sequence number for this student
                next_sequence = cls._get_next_sequence_for_student(
                    student,
                    template.subject,
                    template.academic_period,
                    template.partial_number,
                    template.activity_type
                )
                
                # Create new activity
                activity = Activity(
                    name=template.name,
                    description=template.description,
                    activity_type=template.activity_type,
                    partial_number=template.partial_number,
                    sequence_number=next_sequence,
                    subject=template.subject,
                    student=student,
                    academic_period=template.academic_period
                )
                
                # Validate the new activity
                activity.full_clean()
                activities_to_create.append(activity)
            
            # Bulk create all activities if validation passed
            created_activities = Activity.objects.bulk_create(activities_to_create)
            
        return created_activities
    
    @staticmethod
    def _get_next_sequence_for_student(student, subject, academic_period, partial_number, activity_type) -> int:
        """
        Gets the next available sequence number for a specific student and activity configuration.
        """
        from apps.subjects.models import Activity  # Import here to avoid circular imports
        
        last_sequence = Activity.objects.filter(
            student=student,
            subject=subject,
            academic_period=academic_period,
            partial_number=partial_number,
            activity_type=activity_type
        ).aggregate(Max('sequence_number'))['sequence_number__max'] or 0
        
        return last_sequence + 1

class BulkGradeUpdate:
    @staticmethod
    def update_activity_scores(activity_template, scores_data):
        """
        Actualiza las calificaciones de las actividades relacionadas con un template.
        :param activity_template: Plantilla de actividad
        :param scores_data: Diccionario o lista de diccionarios con los datos de calificación (ej. {student_id: score})
        :return: Lista de actividades actualizadas
        """
        updated_activities = []

        # Obtén todas las actividades relacionadas con el template
        activities = activity_template.get_all_related_activities()

        # Creamos un diccionario para acceder rápidamente a las actividades por estudiante
        activities_dict = {activity.student.id: activity for activity in activities}

        # Inicia la transacción para asegurar que todo sea atómico
        with transaction.atomic():
            for data in scores_data:
                student_id = data.get('student_id')
                score = data.get('score')

                # Verifica si existe la actividad para este estudiante
                if student_id in activities_dict:
                    activity = activities_dict[student_id]
                    
                    # Validar que la calificación esté en el rango adecuado (0 a 10)
                    if not (0 <= score <= 10):
                        raise ValidationError(f"La calificación para el estudiante {student_id} no es válida.")

                    # Asigna la nueva calificación
                    activity.score = Decimal(score)
                    activity.save()  # Guardar la actividad actualizada
                    updated_activities.append(activity)

        return updated_activities