from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.subjects.models.Especialidad import Especialidad

class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField()
    horas_semanales = models.PositiveIntegerField()
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.nombre