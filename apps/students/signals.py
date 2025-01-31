from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.students.models import DetalleMatricula
from apps.subjects.models.academic import Parcial
from apps.subjects.models.activity import Calificacion
from apps.subjects.models.grades import AsignacionProfesor


@receiver(post_save, sender=DetalleMatricula)
def crear_o_actualizar_calificaciones(sender, instance, created, **kwargs):
    periodo = instance.matricula.periodo

    # Buscar la asignación del profesor
    asignaciones = AsignacionProfesor.objects.filter(
        materia=instance.materia,
        curso=instance.matricula.estudiante.curso,
        periodo=periodo
    )

    # Obtener instancias de Parcial para el período
    parciales = Parcial.objects.filter(
        trimestre__periodo=periodo,
        numero__in=[1, 2]  # Para parciales 1 y 2
    )

    for asignacion in asignaciones:
        for parcial in parciales:
            # Verificar si ya existe la calificación
            existing_grade = Calificacion.objects.filter(
                detalle_matricula=instance,
                asignacion_profesor=asignacion,
                parcial=parcial
            ).first()

            if existing_grade:
                # Si existe, no hacer nada (o actualizar si deseas modificar alguna calificación específica)
                pass
            else:
                # Crear una calificación solo si no existe previamente
                Calificacion.objects.create(
                    detalle_matricula=instance,
                    asignacion_profesor=asignacion,
                    parcial=parcial,
                    tarea1=Decimal('1'),
                    tarea2=Decimal('1'),
                    tarea3=Decimal('1'),
                    tarea4=Decimal('1'),
                    examen=Decimal('1'),
                )
