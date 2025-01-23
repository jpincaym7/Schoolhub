from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.subjects.models.Curso import Curso
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia

class AsignacionProfesor(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['profesor', 'materia', 'curso', 'periodo']
        
    def __str__(self):
        return f'{self.materia}'