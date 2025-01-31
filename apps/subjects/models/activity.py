from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import ROUND_DOWN, Decimal
from apps.students.models import DetalleMatricula
from apps.subjects.models.academic import Parcial, Trimestre
from apps.subjects.models.grades import AsignacionProfesor

class Calificacion(models.Model):
    detalle_matricula = models.ForeignKey('students.DetalleMatricula', on_delete=models.CASCADE)
    asignacion_profesor = models.ForeignKey('subjects.AsignacionProfesor', on_delete=models.CASCADE)
    parcial = models.ForeignKey(Parcial, on_delete=models.CASCADE)
    
    # Notas Parciales (60%)
    tarea1 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea2 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea3 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    tarea4 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    
    # Examen Parcial (20%)
    examen = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=1)
    
    # Promedio Final del Parcial
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
    def crear_calificaciones_trimestre(cls, trimestre):
        from apps.students.models import DetalleMatricula
        detalles = DetalleMatricula.objects.filter(matricula__periodo=trimestre.periodo)
        
        for detalle in detalles:
            try:
                asignacion = AsignacionProfesor.objects.get(
                    materia=detalle.materia,
                    curso=detalle.matricula.estudiante.curso,
                    periodo=trimestre.periodo
                )
                
                # Obtener todos los parciales para este trimestre
                parciales = Parcial.objects.filter(trimestre=trimestre)
                
                for parcial in parciales:
                    # Comprobar si ya existen calificaciones para este estudiante en este parcial
                    existing_grade = cls.objects.filter(
                        detalle_matricula=detalle,
                        asignacion_profesor=asignacion,
                        parcial=parcial
                    ).exists()
                    
                    if not existing_grade:
                        # Solo se crean calificaciones si no existen previamente
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
                continue

    def save(self, *args, **kwargs):
        # Definir constantes de peso como Decimales
        PESO_TAREAS = Decimal('0.70')    # 70% para tareas
        PESO_EXAMEN = Decimal('0.30')    # 30% para examen
        PRECISION = Decimal('0.01')      # Precisión de 2 decimales

        # Calcular promedio de tareas (70%)
        tareas = [self.tarea1, self.tarea2, self.tarea3, self.tarea4]
        promedio_tareas = sum(Decimal(str(tarea)) for tarea in tareas) / len(tareas)
        nota_tareas = (promedio_tareas * PESO_TAREAS).quantize(PRECISION, rounding=ROUND_DOWN)

        # Calcular nota del examen (30%)
        nota_examen = (Decimal(str(self.examen)) * PESO_EXAMEN).quantize(PRECISION, rounding=ROUND_DOWN)

        # Calcular promedio final
        self.promedio_final = (nota_tareas + nota_examen).quantize(PRECISION, rounding=ROUND_DOWN)

        self.full_clean()
        super().save(*args, **kwargs)

        # Actualizar promedio del trimestre
        self.actualizar_promedio_trimestre()

    def actualizar_promedio_trimestre(self):
        PromedioTrimestre.actualizar_promedio(
            self.detalle_matricula,
            self.parcial.trimestre
        )

    def __str__(self):
        return f"{self.detalle_matricula.matricula.estudiante} - {self.detalle_matricula.materia} - {self.parcial}"

class PromedioTrimestre(models.Model):
    detalle_matricula = models.ForeignKey('students.DetalleMatricula', on_delete=models.CASCADE)
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    promedio_p1 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_p2 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    examen_trimestral = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_final = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0, editable=False)

    class Meta:
        unique_together = ['detalle_matricula', 'trimestre']

    @classmethod
    def actualizar_promedio(cls, detalle_matricula, trimestre):
        # Constantes de peso para el promedio trimestral
        PESO_PARCIAL = Decimal('0.35')       # 35% cada parcial
        PESO_EXAMEN = Decimal('0.30')        # 30% examen trimestral
        PRECISION = Decimal('0.01')          # Precisión de 2 decimales

        promedio, created = cls.objects.get_or_create(
            detalle_matricula=detalle_matricula,
            trimestre=trimestre
        )

        # Obtener calificaciones del trimestre
        calificaciones = Calificacion.objects.filter(
            detalle_matricula=detalle_matricula,
            parcial__trimestre=trimestre
        )

        # Calcular promedios por parcial
        for calif in calificaciones:
            if calif.parcial.numero == 1:
                promedio.promedio_p1 = calif.promedio_final
            elif calif.parcial.numero == 2:
                promedio.promedio_p2 = calif.promedio_final

        # Calcular promedio final (35% P1 + 35% P2 + 30% Examen trimestral)
        if all([promedio.promedio_p1, promedio.promedio_p2, promedio.examen_trimestral]):
            p1 = (Decimal(str(promedio.promedio_p1)) * PESO_PARCIAL).quantize(PRECISION, rounding=ROUND_DOWN)
            p2 = (Decimal(str(promedio.promedio_p2)) * PESO_PARCIAL).quantize(PRECISION, rounding=ROUND_DOWN)
            examen = (Decimal(str(promedio.examen_trimestral)) * PESO_EXAMEN).quantize(PRECISION, rounding=ROUND_DOWN)
            
            promedio.promedio_final = (p1 + p2 + examen).quantize(PRECISION, rounding=ROUND_DOWN)
        
        promedio.save()

    def __str__(self):
        return f"Promedio Trimestral: {self.detalle_matricula.matricula.estudiante} - {self.trimestre}"

class PromedioAnual(models.Model):
    detalle_matricula = models.OneToOneField('students.DetalleMatricula', on_delete=models.CASCADE)
    promedio_t1 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_t2 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_t3 = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    promedio_final = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)], default=0, editable=False)

    def save(self, *args, **kwargs):
        PRECISION = Decimal('0.01')  # Precisión de 2 decimales

        if all([self.promedio_t1, self.promedio_t2, self.promedio_t3]):
            # Calcular promedio final (promedio simple de los tres trimestres)
            suma = sum(Decimal(str(x)) for x in [self.promedio_t1, self.promedio_t2, self.promedio_t3])
            self.promedio_final = (suma / 3).quantize(PRECISION, rounding=ROUND_DOWN)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Promedio Anual: {self.detalle_matricula.matricula.estudiante} - {self.detalle_matricula.materia}"