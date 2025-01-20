from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from typing import List, Dict
from django.utils import timezone
from django.db.models import Max

class ActivityTemplate(models.Model):
    """Template for creating activities in bulk"""
    name = models.CharField(max_length=100, verbose_name=_('Nombre'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    activity_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', _('Individual')),
            ('group', _('Grupal')),
        ],
        verbose_name=_('Tipo de Actividad')
    )
    partial_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name=_('Número de Parcial')
    )
    sequence_number = models.PositiveSmallIntegerField(
        editable=False,
        verbose_name=_('Número de Secuencia')
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        verbose_name=_('Materia')
    )
    academic_period = models.ForeignKey(
        'AcademicPeriod',
        on_delete=models.CASCADE,
        verbose_name=_('Período Académico')
    )

    class Meta:
        verbose_name = _('Plantilla de Actividad')
        verbose_name_plural = _('Plantillas de Actividades')
        unique_together = [
            'subject', 'academic_period',
            'partial_number', 'activity_type', 'sequence_number'
        ]

    def create_activities_for_students(self, students):
        """Create activities for multiple students based on this template"""
        activities = []
        for student in students:
            activity = Activity.objects.create(
                name=self.name,
                description=self.description,
                activity_type=self.activity_type,
                partial_number=self.partial_number,
                sequence_number=self.sequence_number,
                subject=self.subject,
                academic_period=self.academic_period,
                student=student,
                template=self
            )
            activities.append(activity)
        return activities

    def get_next_sequence(self):
        """Obtiene el siguiente número de secuencia disponible"""
        last_sequence = ActivityTemplate.objects.filter(
            subject=self.subject,
            academic_period=self.academic_period,
            partial_number=self.partial_number,
            activity_type=self.activity_type
        ).aggregate(Max('sequence_number'))['sequence_number__max'] or 0
        return last_sequence + 1

    def get_all_related_activities(self):
        """Obtiene todas las actividades creadas a partir de esta plantilla"""
        return Activity.objects.filter(template=self)

    def get_all_students_with_activity(self):
        """Obtiene todos los estudiantes que tienen actividades creadas a partir de esta plantilla"""
        return self.get_all_related_activities().select_related('student')

    def clean(self):
        """Validación para asegurar que sequence_number sea único y que no haya más de 2 secuencias por tipo de actividad"""
        super().clean()
        
        # Validar que no se excedan las 2 secuencias para el tipo de actividad
        sequence_count = ActivityTemplate.objects.filter(
            subject=self.subject,
            academic_period=self.academic_period,
            partial_number=self.partial_number,
            activity_type=self.activity_type
        ).count()
        
        if sequence_count >= 2:
            raise ValidationError({
                'sequence_number': _(
                    "No puede haber más de 2 secuencias para el mismo tipo de actividad (individual o grupal)."
                )
            })
        
        # Validación de secuencias duplicadas
        if ActivityTemplate.objects.filter(
            subject=self.subject,
            academic_period=self.academic_period,
            partial_number=self.partial_number,
            activity_type=self.activity_type,
            sequence_number=self.sequence_number,
        ).exclude(pk=self.pk).exists():
            raise ValidationError({
                'sequence_number': _(
                    "Ya existe una plantilla con esta secuencia para la misma materia, período académico, parcial y tipo de actividad."
                )
            })

    def save(self, *args, **kwargs):
        """Asigna automáticamente sequence_number si no está definido"""
        if not self.pk:  # Solo asignar en la creación
            self.sequence_number = self.get_next_sequence()
        self.full_clean()  # Ejecuta validaciones
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.subject} - P{self.partial_number}"

class Activity(models.Model):
    """Base model for academic activities"""
    ACTIVITY_TYPES = [
        ('individual', _('Individual')),
        ('group', _('Grupal')),
    ]

    name = models.CharField(max_length=100, verbose_name=_('Nombre'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        verbose_name=_('Tipo de Actividad')
    )
    partial_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name=_('Número de Parcial')
    )
    sequence_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        verbose_name=_('Número de Secuencia')
    )
    score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
        verbose_name=_('Calificación')
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        verbose_name=_('Materia')
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('Estudiante')
    )
    academic_period = models.ForeignKey(
        'AcademicPeriod',
        on_delete=models.CASCADE,
        verbose_name=_('Período Académico')
    )
    # Nueva relación con la plantilla que generó esta actividad
    template = models.ForeignKey(
        ActivityTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities',
        verbose_name=_('Plantilla de Actividad')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Actividad')
        verbose_name_plural = _('Actividades')
        unique_together = [
            'student', 'subject', 'academic_period',
            'partial_number', 'activity_type', 'sequence_number'
        ]
        ordering = ['partial_number', 'activity_type', 'sequence_number']

    @classmethod
    def get_activities_by_template(cls, template_id):
        """Obtiene todas las actividades creadas a partir de una plantilla específica"""
        return cls.objects.filter(template_id=template_id)

    @classmethod
    def get_students_by_template(cls, template_id):
        """Obtiene todos los estudiantes que tienen una actividad creada a partir de una plantilla específica"""
        return cls.objects.filter(template_id=template_id).select_related('student')

    def clean(self):
        # Validar que no haya una actividad existente con los mismos datos
        if self.pk is None:
            existing_activity = Activity.objects.filter(
                student=self.student,
                subject=self.subject,
                academic_period=self.academic_period,
                partial_number=self.partial_number,
                activity_type=self.activity_type,
                sequence_number=self.sequence_number
            ).exists()

            if existing_activity:
                raise ValidationError(_('Ya existe una actividad con los mismos datos.'))

    @classmethod
    def bulk_create_from_template(cls, activity_template, students):
        activities = activity_template.create_activities_for_students(students)
        # Asignar la plantilla a todas las actividades creadas
        for activity in activities:
            activity.template = activity_template
        return activities

    @classmethod
    def bulk_update_scores(cls, activity_template, scores_data):
        from .utils import BulkGradeUpdate
        return BulkGradeUpdate.update_activity_scores(activity_template, scores_data)