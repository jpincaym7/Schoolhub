from django.db import models
from apps.students.models import Student
from apps.users.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# Create your models here.
class Communication(models.Model):
    """
    Modelo para comunicaciones entre padres y profesores
    """
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='communications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Comunicación')
        verbose_name_plural = _('Comunicaciones')
        
class TeacherOfficeHours(models.Model):
    """
    Modelo para gestionar los horarios de atención de los profesores
    """
    DAYS_OF_WEEK = (
        (0, _('Lunes')),
        (1, _('Martes')), 
        (2, _('Miércoles')),
        (3, _('Jueves')),
        (4, _('Viernes')),
        (5, _('Sábado')),
        (6, _('Domingo'))
    )

    teacher = models.ForeignKey(
        'users.User',  # Asumiendo que User es tu modelo de usuario
        on_delete=models.CASCADE,
        related_name='office_hours',
        verbose_name=_('Profesor'),
        limit_choices_to={'user_type': 'teacher'},
        null=True
    )
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name=_('Día de la semana')
    )
    start_time = models.TimeField(
        verbose_name=_('Hora de inicio')
    )
    end_time = models.TimeField(
        verbose_name=_('Hora de fin')
    )
    location = models.CharField(
        max_length=100,
        verbose_name=_('Ubicación'),
        help_text=_('Oficina o lugar de atención')
    )
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('Descripción adicional o notas sobre el horario de atención'),
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Horario de Atención')
        verbose_name_plural = _('Horarios de Atención')
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'day_of_week', 'start_time'],
                name='unique_office_hours'
            )
        ]

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def clean(self):
        """
        Validación personalizada para evitar solapamiento de horarios
        """
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': _('La hora de fin debe ser posterior a la hora de inicio')
                })

            # Verificar solapamiento de horarios
            overlapping_hours = TeacherOfficeHours.objects.filter(
                teacher=self.teacher,
                day_of_week=self.day_of_week,
                is_active=True
            ).exclude(pk=self.pk)

            for hours in overlapping_hours:
                if (self.start_time <= hours.end_time and 
                    self.end_time >= hours.start_time):
                    raise ValidationError(
                        _('Este horario se solapa con otro horario de atención existente')
                    )