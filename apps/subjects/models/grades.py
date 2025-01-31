from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.subjects.models.Curso import Curso
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from apps.subjects.models.subject import Materia

class AsignacionProfesorTrimestre(models.Model):
    asignacion = models.ForeignKey('AsignacionProfesor', on_delete=models.CASCADE, related_name='asignaciones_trimestre')
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['asignacion', 'trimestre']

class AsignacionProfesor(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    trimestres = models.ManyToManyField(Trimestre, through=AsignacionProfesorTrimestre)
    
    class Meta:
        unique_together = ['profesor', 'materia', 'curso', 'periodo']
        
    def clean(self):
        if not self.pk:
            existing_assignment = AsignacionProfesor.objects.filter(
                materia=self.materia,
                curso=self.curso,
                periodo=self.periodo
            ).exclude(profesor=self.profesor).first()
            
            if existing_assignment:
                error_message = {
                    "error": "duplicate_assignment",
                    "detail": f"La materia {self.materia} ya está asignada al profesor {existing_assignment.profesor} en el curso {self.curso} para el periodo {self.periodo}",
                    "code": "assignment_conflict",
                    "current_teacher": str(existing_assignment.profesor),
                    "subject": str(self.materia),
                    "course": str(self.curso),
                    "period": str(self.periodo)
                }
                raise ValidationError(error_message)
    
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Si es una nueva asignación, crear las asignaciones por trimestre
        if is_new:
            curso_trimestres = self.curso.trimestres.all()
            for trimestre in curso_trimestres:
                AsignacionProfesorTrimestre.objects.get_or_create(
                    asignacion=self,
                    trimestre=trimestre
                )
        
    def __str__(self):
        return f'{self.materia}'