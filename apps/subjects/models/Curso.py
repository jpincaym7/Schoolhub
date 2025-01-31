from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.academic import PeriodoAcademico, Trimestre

class Curso(models.Model):
    NIVELES = (
        ('6', 'Sexto'),
    )
    
    nombre = models.CharField(max_length=100)
    nivel = models.CharField(max_length=1, choices=NIVELES)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    trimestres = models.ManyToManyField(Trimestre, blank=True)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return f"{self.get_nivel_display()} {self.especialidad.nombre}"

    def save(self, *args, **kwargs):
        # Primero guardamos el curso
        super().save(*args, **kwargs)
        
        # Después de guardar, nos aseguramos de que tenga los tres trimestres
        if self.periodo:
            for num_trimestre in ['1', '2', '3']:
                trimestre, created = Trimestre.objects.get_or_create(
                    periodo=self.periodo,
                    trimestre=num_trimestre
                )
                self.trimestres.add(trimestre)
