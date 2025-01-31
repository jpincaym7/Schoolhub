from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.subjects.models.Especialidad import Especialidad
from django.db.models.deletion import ProtectedError


class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField()
    horas_semanales = models.PositiveIntegerField()
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    
    def has_grades(self):
        """
        Check if the subject has any associated grades
        """
        # We need to import here to avoid circular imports
        from apps.subjects.models.activity import Calificacion
        return Calificacion.objects.filter(
            detalle_matricula__materia=self
        ).exists()
    
    def delete(self, *args, **kwargs):
        """
        Override delete method to prevent deletion if grades exist
        """
        if self.has_grades():
            raise ProtectedError(
                _("No se puede eliminar la materia porque tiene calificaciones asociadas."),
                self.__class__.objects.none()
            )
            
        # Also check if there are any teacher assignments
        if hasattr(self, 'asignacionprofesor_set') and self.asignacionprofesor_set.exists():
            raise ProtectedError(
                _("No se puede eliminar la materia porque tiene profesores asignados."),
                self.__class__.objects.none()
            )
            
        return super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = _("Materia")
        verbose_name_plural = _("Materias")