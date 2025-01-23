from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.subjects.models.Especialidad import Especialidad  # Adjust import as needed
from apps.students.models import Estudiante
from apps.subjects.models.Teacher import Profesor

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create corresponding Estudiante or Profesor profile when a User is created
    """
    if created:
        if instance.user_type == 'estudiante':
            # Create Estudiante profile
            Estudiante.objects.create(usuario=instance)
        elif instance.user_type == 'teacher':
            # Fetch a default specialty or handle specialty selection
            default_specialty = Especialidad.objects.first()  # You might want to modify this
            if default_specialty:
                Profesor.objects.create(
                    usuario=instance,
                    especialidad=default_specialty
                )