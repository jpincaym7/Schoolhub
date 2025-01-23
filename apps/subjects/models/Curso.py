from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.academic import PeriodoAcademico

class Curso(models.Model):
    NIVELES = (
        ('6', 'Sexto'),
    )
    
    nombre = models.CharField(max_length=100)
    nivel = models.CharField(max_length=1, choices=NIVELES)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.get_nivel_display()} {self.especialidad.nombre}"
