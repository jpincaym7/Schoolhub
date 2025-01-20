from django.db import models
from apps.users.models import User
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """
    Modelo para notificaciones del sistema
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=[
        ('grade', 'Calificación'),
        ('attendance', 'Asistencia'),
        ('behavior', 'Comportamiento'),
        ('message', 'Mensaje'),
        ('system', 'Sistema')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Notificación')
        verbose_name_plural = _('Notificaciones')