from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.subject import Materia
from apps.users.models import User

class Profesor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    materias = models.ManyToManyField(Materia, through='AsignacionProfesor')
    
    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"