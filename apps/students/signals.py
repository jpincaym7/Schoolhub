# signals.py
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.students.models import DetalleMatricula
from apps.subjects.models.activity import Calificacion
from apps.subjects.models.grades import  AsignacionProfesor


@receiver(post_save, sender=DetalleMatricula)
def crear_calificaciones_por_defecto(sender, instance, created, **kwargs):
    if created:  # Solo se ejecuta cuando se crea un nuevo DetalleMatricula
        # Obtener el periodo académico de la matrícula
        periodo = instance.matricula.periodo
        
        # Buscar la asignación del profesor para la materia y curso correspondiente
        asignaciones = AsignacionProfesor.objects.filter(
            materia=instance.materia,
            curso=instance.matricula.estudiante.curso,
            periodo=periodo
        )

        # Crear calificaciones por cada parcial para cada asignación
        for asignacion in asignaciones:
            for parcial in [1, 2]:  # Primer y Segundo Parcial
                Calificacion.objects.get_or_create(
                    detalle_matricula=instance,
                    asignacion_profesor=asignacion,
                    parcial=parcial,
                    defaults={
                        'tarea1': Decimal('1'),
                        'tarea2': Decimal('1'),
                        'tarea3': Decimal('1'),
                        'tarea4': Decimal('1'),
                        'examen': Decimal('1'),
                    }
                )
