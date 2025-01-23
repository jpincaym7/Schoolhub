from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
from decimal import Decimal, ROUND_DOWN
from apps.subjects.models.activity import Calificacion, PromedioAnual

@receiver(post_save, sender=Calificacion)
def update_annual_average(sender, instance, **kwargs):
    # Find all grades for this student's specific subject and period
    calificaciones = Calificacion.objects.filter(
        detalle_matricula=instance.detalle_matricula,
        asignacion_profesor=instance.asignacion_profesor
    )

    # Check if we have grades for both partial exams
    parciales_completos = calificaciones.count() == 2 and \
        all(calif.promedio_final != 0 for calif in calificaciones)

    if parciales_completos:
        # Get the PromedioAnual instance or create if not exists
        promedio_anual, _ = PromedioAnual.objects.get_or_create(
            detalle_matricula=instance.detalle_matricula
        )

        # Assign partial grades
        for calif in calificaciones:
            if calif.parcial == 1:
                promedio_anual.promedio_p1 = calif.promedio_final
            elif calif.parcial == 2:
                promedio_anual.promedio_p2 = calif.promedio_final

        # Calculate final average
        promedio_anual.promedio_final = (
            promedio_anual.promedio_p1 + promedio_anual.promedio_p2
        ) / 2

        # Round to 2 decimal places
        promedio_anual.promedio_final = Decimal(
            str(promedio_anual.promedio_final)
        ).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        promedio_anual.save()