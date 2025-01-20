from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.subjects.models import (
    Activity,
    AcademicPeriod,
    Subject,
)
class PartialGrade(models.Model):
    """Manages partial grades"""
    PASSING_GRADE = Decimal('7.00')
    MAX_GRADE = Decimal('10.00')
    REQUIRED_ACTIVITIES = 2  # Number of required activities per type

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='partial_grades',
        verbose_name=_('Estudiante')
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        verbose_name=_('Materia')
    )
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        verbose_name=_('Período Académico')
    )
    partial_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name=_('Número de Parcial')
    )
    evaluation_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
        verbose_name=_('Nota Evaluación')
    )
    final_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
        editable=False,
        verbose_name=_('Nota Final')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Calificación Parcial')
        verbose_name_plural = _('Calificaciones Parciales')
        unique_together = ['student', 'subject', 'academic_period', 'partial_number']
        ordering = ['academic_period', 'partial_number']

    def get_activities_status(self):
        """Get the status of required activities"""
        activities = Activity.objects.filter(
            student=self.student,
            subject=self.subject,
            academic_period=self.academic_period,
            partial_number=self.partial_number
        )
        
        status = {
            'individual_count': activities.filter(activity_type='individual').count(),
            'group_count': activities.filter(activity_type='group').count(),
            'is_complete': False,
            'missing_activities': []
        }
        
        if status['individual_count'] < self.REQUIRED_ACTIVITIES:
            status['missing_activities'].append(
                f'Faltan {self.REQUIRED_ACTIVITIES - status["individual_count"]} actividades individuales'
            )
            
        if status['group_count'] < self.REQUIRED_ACTIVITIES:
            status['missing_activities'].append(
                f'Faltan {self.REQUIRED_ACTIVITIES - status["group_count"]} actividades grupales'
            )
            
        status['is_complete'] = len(status['missing_activities']) == 0
        return status

    def clean(self):
        """Validate grade constraints"""
        super().clean()
        
        if self.evaluation_score > self.MAX_GRADE:
            raise ValidationError(_('La calificación no puede superar los 10 puntos'))
        
        # Check if all required activities are present
        status = self.get_activities_status()
        if not status['is_complete']:
            raise ValidationError(_(', '.join(status['missing_activities'])))

    def calculate_final_score(self):
        """Calculate final score based on activities and evaluation"""
        status = self.get_activities_status()
        if not status['is_complete']:
            return Decimal('0.00')

        activities = Activity.objects.filter(
            student=self.student,
            subject=self.subject,
            academic_period=self.academic_period,
            partial_number=self.partial_number
        )

        # Get best 2 scores for each type
        individual_scores = activities.filter(
            activity_type='individual'
        ).order_by('-score')[:2].values_list('score', flat=True)
        
        group_scores = activities.filter(
            activity_type='group'
        ).order_by('-score')[:2].values_list('score', flat=True)

        # Calculate averages
        individual_avg = sum(individual_scores) / len(individual_scores)
        group_avg = sum(group_scores) / len(group_scores)

        # Calculate weighted final score
        final_score = (
            (individual_avg * Decimal('0.3')) +  # 30% individual
            (group_avg * Decimal('0.3')) +       # 30% group
            (self.evaluation_score * Decimal('0.4'))  # 40% evaluation
        )

        return round(final_score, 2)

    def save(self, *args, **kwargs):
        # Calculate final score before saving
        self.final_score = self.calculate_final_score()
        super().save(*args, **kwargs)
        
        # Try to update or create quimester grade
        QuimesterGrade.objects.update_or_create_from_partial(self)

    def __str__(self):
        return f"{self.student} - {self.subject} - Q{self.academic_period.number}P{self.partial_number}"

class QuimesterGradeManager(models.Manager):
    def update_or_create_from_partial(self, partial_grade):
        """Update or create quimester grade when a partial is saved"""
        # Get all partial grades for this student/subject/period
        partials = PartialGrade.objects.filter(
            student=partial_grade.student,
            subject=partial_grade.subject,
            academic_period=partial_grade.academic_period
        )
        
        # Only create/update quimester grade if all partials are complete
        if partials.count() == 3:
            # Calculate average of partial final scores
            final_score = sum(p.final_score for p in partials) / 3
            
            # Update or create the quimester grade
            return self.update_or_create(
                student=partial_grade.student,
                subject=partial_grade.subject,
                academic_period=partial_grade.academic_period,
                defaults={'final_score': round(final_score, 2)}
            )
        return None, False

class QuimesterGrade(models.Model):
    """Manages quimester grades"""
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='quimester_grades',
        verbose_name=_('Estudiante')
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        verbose_name=_('Materia')
    )
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        verbose_name=_('Período Académico')
    )
    final_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
        verbose_name=_('Nota Final')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = QuimesterGradeManager()

    class Meta:
        verbose_name = _('Calificación Quimestral')
        verbose_name_plural = _('Calificaciones Quimestrales')
        unique_together = ['student', 'subject', 'academic_period']
        ordering = ['academic_period']

    def __str__(self):
        return f"{self.student} - {self.subject} - Quimestre {self.academic_period.number}"