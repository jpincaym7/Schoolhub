from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.subject import Subject
from apps.users.models import User
from django.core.exceptions import ValidationError
from datetime import date

class Student(models.Model):
    """
    Modelo para almacenar información de estudiantes
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    birth_date = models.DateField()
    parent = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='students', 
        limit_choices_to={'user_type': 'parent'},
        null=True,  # Permite valores nulos
        blank=True  # Permite dejar el campo en blanco
    )
    grade = models.CharField(max_length=50)  # Ej: "Tercero BGU"
    parallel = models.CharField(max_length=1)  # Ej: "A", "B", etc.
    academic_year = models.CharField(max_length=9)  # Ej: "2024-2025"
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(
        upload_to='students/photos/',
        blank=True,
        null=True,
        verbose_name=_('Foto del estudiante')
    )

    class Meta:
        verbose_name = _('Estudiante')
        verbose_name_plural = _('Estudiantes')
        unique_together = ['student_id', 'academic_year']
    
    def get_full_name(self):
        """
        Devuelve el nombre completo del estudiante.
        """
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.get_full_name()

class Attendance(models.Model):
    """
    Modelo para registro de asistencia
    """
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=15, choices=[
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('late', 'Atrasado'),
        ('justified', 'Justificado')
    ])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Asistencia')
        verbose_name_plural = _('Asistencias')
        unique_together = ['student', 'date']

    def clean(self):
        """
        Validaciones personalizadas antes de guardar
        """
        # Validar que no se registre asistencia en fechas futuras
        if self.date > date.today():
            raise ValidationError({
                'date': _('No se puede registrar asistencia para fechas futuras.')
            })
        
        # Validar si ya existe un registro para el mismo estudiante en la misma fecha
        if not self.pk:  # Solo para nuevos registros
            existing_attendance = Attendance.objects.filter(
                student=self.student,
                date=self.date
            ).exists()
            
            if existing_attendance:
                raise ValidationError({
                    'student': _('Ya existe un registro de asistencia para este estudiante en esta fecha.')
                })

        # Validar que solo se pueda justificar dentro de los 3 días posteriores
        if self.status == 'justified':
            days_difference = date.today() - self.date
            if days_difference.days > 3:
                raise ValidationError({
                    'status': _('No se puede justificar una asistencia después de 3 días.')
                })

    def save(self, *args, **kwargs):
        """
        Sobrescribimos el método save para ejecutar las validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)

class Behavior(models.Model):
    """
    Modelo para registro de comportamiento de estudiantes
    """
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='behaviors')
    date = models.DateField()
    type = models.CharField(max_length=15, choices=[
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
        ('neutral', 'Neutral')
    ])
    description = models.TextField()
    reported_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    academic_period = models.ForeignKey(
        'subjects.AcademicPeriod',
        on_delete=models.CASCADE,
        verbose_name=_('Período Académico'),
        default=1
    )
    partial_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name=_('Número de Parcial'),
        default=1
    )
    
    class Meta:
        verbose_name = _('Comportamiento')
        verbose_name_plural = _('Comportamientos')

    def clean(self):
        if self.date > date.today():
            raise ValidationError({
                'date': _('No se puede registrar comportamiento para fechas futuras.')
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Actualizar el resumen después de guardar
        BehaviorSummary.update_for_student(self.student, self.academic_period)

    def __str__(self):
        return f"{self.student} - {self.get_type_display()} - {self.date}"

class BehaviorSummary(models.Model):
    """
    Modelo para registrar el resumen de comportamiento por quimestre
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='behavior_summaries'
    )
    academic_period = models.ForeignKey(
        'subjects.AcademicPeriod',
        on_delete=models.CASCADE,
        default=1
    )
    positive_count = models.PositiveIntegerField(default=0)
    negative_count = models.PositiveIntegerField(default=0)
    neutral_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Resumen de Comportamiento')
        verbose_name_plural = _('Resúmenes de Comportamiento')
        unique_together = ['student', 'academic_period']

    @classmethod
    def update_for_student(cls, student, academic_period):
        """
        Actualiza o crea el resumen de comportamiento para un estudiante en un período específico
        """
        behaviors = Behavior.objects.filter(
            student=student,
            academic_period=academic_period
        )

        summary, created = cls.objects.get_or_create(
            student=student,
            academic_period=academic_period,
            defaults={
                'positive_count': behaviors.filter(type='positive').count(),
                'negative_count': behaviors.filter(type='negative').count(),
                'neutral_count': behaviors.filter(type='neutral').count()
            }
        )

        if not created:
            summary.positive_count = behaviors.filter(type='positive').count()
            summary.negative_count = behaviors.filter(type='negative').count()
            summary.neutral_count = behaviors.filter(type='neutral').count()
            summary.save()

    def get_partial_counts(self, partial_number):
        """
        Obtiene el conteo de comportamientos para un parcial específico
        """
        behaviors = Behavior.objects.filter(
            student=self.student,
            academic_period=self.academic_period,
            partial_number=partial_number
        )
        
        return {
            'positive': behaviors.filter(type='positive').count(),
            'negative': behaviors.filter(type='negative').count(),
            'neutral': behaviors.filter(type='neutral').count()
        }

    def __str__(self):
        return f"Resumen {self.student} - Quimestre {self.academic_period.number}"

