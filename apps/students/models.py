from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.Curso import Curso
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from apps.subjects.models.subject import Materia
from apps.users.models import User
from django.core.exceptions import ValidationError
from datetime import date

class Estudiante(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, null=True)
    
    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, null=True)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, null=True)
    materias = models.ManyToManyField(Materia, through='DetalleMatricula', null=True)
    numero_matricula = models.CharField(max_length=10, unique=True, null=True)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['estudiante', 'periodo']

    def __str__(self):
        return f"Matrícula {self.numero_matricula}: {self.estudiante} ({self.periodo})"

class DetalleMatricula(models.Model):
    matricula = models.ForeignKey(Matricula, related_name='detallematricula_set', on_delete=models.CASCADE, null=True)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=True)
    fecha_agregada = models.DateTimeField(auto_now_add=True)
    trimestres = models.ManyToManyField(Trimestre, through='DetalleMatriculaTrimestre')
    
    class Meta:
        unique_together = ['matricula', 'materia']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Obtener los trimestres del curso del estudiante
            curso_trimestres = self.matricula.estudiante.curso.trimestres.all()
            # Crear registro para cada trimestre
            for trimestre in curso_trimestres:
                DetalleMatriculaTrimestre.objects.get_or_create(
                    detalle_matricula=self,
                    trimestre=trimestre
                )

    def __str__(self):
        return f"{self.matricula.estudiante} - {self.materia}"

class DetalleMatriculaTrimestre(models.Model):
    detalle_matricula = models.ForeignKey(DetalleMatricula, on_delete=models.CASCADE, related_name='detalles_trimestre')
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['detalle_matricula', 'trimestre']