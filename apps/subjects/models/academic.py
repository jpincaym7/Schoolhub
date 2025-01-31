from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class PeriodoAcademico(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
    
class Trimestre(models.Model):
    TRIMESTRES = (
        ('1', 'Primer Trimestre'),
        ('2', 'Segundo Trimestre'),
        ('3', 'Tercer Trimestre'),
    )

    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, related_name="trimestres")
    trimestre = models.CharField(max_length=1, choices=TRIMESTRES)

    class Meta:
        unique_together = ('periodo', 'trimestre')

    def __str__(self):
        return f"{self.get_trimestre_display()} - {self.periodo.nombre}"

class Parcial(models.Model):
    PARCIAL_CHOICES = [
        (1, 'Primer Parcial'),
        (2, 'Segundo Parcial')
    ]
    
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE, related_name='parciales')
    numero = models.IntegerField(choices=PARCIAL_CHOICES)

    class Meta:
        unique_together = ('trimestre', 'numero')

    def __str__(self):
        return f"{self.get_numero_display()} - {self.trimestre}"