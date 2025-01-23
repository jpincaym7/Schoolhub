from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import ROUND_DOWN, Decimal
from apps.students.models import DetalleMatricula
from apps.subjects.models.grades import AsignacionProfesor

class Calificacion(models.Model):
    PARCIAL_CHOICES = [
        (1, 'Primer Parcial'),
        (2, 'Segundo Parcial')
    ]
    
    detalle_matricula = models.ForeignKey(DetalleMatricula, on_delete=models.CASCADE)
    asignacion_profesor = models.ForeignKey(AsignacionProfesor, on_delete=models.CASCADE)
    parcial = models.IntegerField(choices=PARCIAL_CHOICES, default=1)
    
    # Notas Parciales (80%)
    tarea1 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea2 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea3 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea4 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    
    # Examen Parcial (20%)
    examen = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    
    # Promedio Final
    promedio_final = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1, editable=False)
    
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ['detalle_matricula', 'asignacion_profesor', 'parcial']

    def clean(self):
        if not hasattr(self, 'detalle_matricula') or not hasattr(self, 'asignacion_profesor'):
            return
        
        if self.detalle_matricula.materia != self.asignacion_profesor.materia:
            raise ValidationError('La materia de la matrícula no coincide con la materia asignada al profesor')
        
        if self.detalle_matricula.matricula.periodo != self.asignacion_profesor.periodo:
            raise ValidationError('Los períodos académicos no coinciden')

    @classmethod
    def crear_calificaciones_periodo(cls, periodo):
        from apps.students.models import DetalleMatricula
        detalles = DetalleMatricula.objects.filter(matricula__periodo=periodo)
        
        for detalle in detalles:
            try:
                asignacion = AsignacionProfesor.objects.get(
                    materia=detalle.materia,
                    curso=detalle.matricula.estudiante.curso,
                    periodo=periodo
                )
                
                # Check existing grades for this subject and student
                existing_subject_grades = cls.objects.filter(
                    detalle_matricula=detalle,
                    asignacion_profesor=asignacion
                )
                
                # Create grades only if no grades exist or all grades are default (one)
                if not existing_subject_grades.exists() or \
                all(
                    calif.tarea1 == 1 and calif.tarea2 == 1 and 
                    calif.tarea3 == 1 and calif.tarea4 == 1 and 
                    calif.examen == 1 
                    for calif in existing_subject_grades
                ):
                    for parcial in [1, 2]:
                        # Check if grade for this partial already exists
                        existing_partial_grade = cls.objects.filter(
                            detalle_matricula=detalle,
                            asignacion_profesor=asignacion,
                            parcial=parcial
                        ).exists()
                        
                        if not existing_partial_grade:
                            cls.objects.create(
                                detalle_matricula=detalle,
                                asignacion_profesor=asignacion,
                                parcial=parcial,
                                tarea1=1,
                                tarea2=1,
                                tarea3=1,
                                tarea4=1,
                                examen=1
                            )
                
            except AsignacionProfesor.DoesNotExist:
                # Skip if no professor assignment exists for this subject and course
                continue

    def save(self, *args, **kwargs):
        from apps.subjects.models.activity import PromedioAnual

        # Convert float constants to Decimal
        peso_tareas = Decimal('0.8')
        peso_examen = Decimal('0.2')

        # Calcular promedio de tareas (80%)
        promedio_tareas = (self.tarea1 + self.tarea2 + self.tarea3 + self.tarea4) / 4
        nota_tareas = promedio_tareas * peso_tareas

        # Calcular nota del examen (20%)
        nota_examen = self.examen * peso_examen

        # Calcular promedio final
        self.promedio_final = nota_tareas + nota_examen

        # Redondear a 2 decimales para evitar errores de validación
        self.promedio_final = self.promedio_final.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        # Realizar validaciones personalizadas
        self.full_clean()

        # Guardar la calificación actual
        super().save(*args, **kwargs)

        # Actualizar o crear el PromedioAnual relacionado
        promedio_anual, created = PromedioAnual.objects.get_or_create(
            detalle_matricula=self.detalle_matricula,
            defaults={'promedio_p1': 0, 'promedio_p2': 0}
        )

        # Actualizar el promedio correspondiente al parcial
        if self.parcial == 1:
            promedio_anual.promedio_p1 = self.promedio_final
        elif self.parcial == 2:
            promedio_anual.promedio_p2 = self.promedio_final

        # Calcular el promedio final si ambos parciales están completos
        if promedio_anual.promedio_p1 != 0 and promedio_anual.promedio_p2 != 0:
            promedio_anual.promedio_final = (
                promedio_anual.promedio_p1 + promedio_anual.promedio_p2
            ) / 2
        else:
            promedio_anual.promedio_final = 0  # Si falta algún parcial, el promedio final es 0

        promedio_anual.save()

    def __str__(self):
        return f"{self.detalle_matricula.matricula.estudiante} - {self.detalle_matricula.materia} - P{self.parcial}"

class PromedioAnual(models.Model):
    detalle_matricula = models.OneToOneField(DetalleMatricula, on_delete=models.CASCADE)
    promedio_p1 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_p2 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_final = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], editable=False)
    
    def clean(self):
        # Validación: no permitir guardar el promedio final si aún no hay promedios para los parciales
        if self.promedio_p1 < 0 or self.promedio_p2 < 0:
            raise ValidationError('No se puede calcular el promedio final si no existen promedios para los parciales.')
    
    def save(self, *args, **kwargs):
        # Realizar la validación antes de guardar
        self.full_clean()  # Llama a la validación personalizada de `clean`
        
        # Calcular promedio final si los parciales están completos
        if self.promedio_p1 != 0 and self.promedio_p2 != 0:
            self.promedio_final = (self.promedio_p1 + self.promedio_p2) / 2
        else:
            self.promedio_final = 0  # Si no hay promedios, dejamos el promedio final en 0

        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Promedio Anual: {self.detalle_matricula.matricula.estudiante} - {self.detalle_matricula.materia}"
