from django.db import models
from apps.students.models import Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.users.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class Communication(models.Model):
    """
    Modelo para comunicaciones entre padres y profesores
    """
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    student = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='communications')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Comunicación')
        verbose_name_plural = _('Comunicaciones')
        
class Comportamiento(models.Model):
    TIPOS_COMPORTAMIENTO = (
        ('A', 'A - Muy Satisfactorio'),
        ('B', 'B - Satisfactorio'),
        ('C', 'C - Poco Satisfactorio'),
        ('D', 'D - Mejorable'),
        ('E', 'E - Insatisfactorio'),
    )
    
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    quimestre = models.CharField(max_length=1, choices=(('1', 'Primer'), ('2', 'Segundo')))
    calificacion = models.CharField(max_length=1, choices=TIPOS_COMPORTAMIENTO)
    observacion = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['estudiante', 'periodo', 'quimestre']
        
class Asistencia(models.Model):
    matricula = models.ForeignKey('students.Matricula', on_delete=models.CASCADE)
    fecha = models.DateField()
    asistio = models.BooleanField(default=True)
    justificacion = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['matricula', 'fecha']
        ordering = ['-fecha', 'matricula']

    def clean(self):
        if self.fecha > timezone.now().date():
            raise ValidationError({
                'fecha': 'No se pueden registrar asistencias en fechas futuras.'
            })
        
        # Verificar que la fecha esté dentro del período académico de la matrícula
        if (self.fecha < self.matricula.periodo.fecha_inicio or 
            self.fecha > self.matricula.periodo.fecha_fin):
            raise ValidationError({
                'fecha': 'La fecha debe estar dentro del período académico.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)