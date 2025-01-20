from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Subject(models.Model):
    """
    Modelo para materias/asignaturas
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    credits = models.PositiveSmallIntegerField()
    teacher = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, 
                              limit_choices_to={'user_type': 'teacher'})

    class Meta:
        verbose_name = _('Asignatura')
        verbose_name_plural = _('Asignaturas')
    
    def __str__(self):
        return self.name