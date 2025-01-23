from django.db import models
from django.contrib.auth.models import AbstractUser
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Modelo base para usuarios del sistema extendiendo AbstractUser de Django
    """
    USER_TYPE_CHOICES = (
        ('admin', 'Administrador'),
        ('teacher', 'Profesor'),
        ('estudiante', 'Estudiante'),
    )
    
    
    profile_image = models.ImageField(
        upload_to='users/profile_images/',
        blank=True,
        null=True,
        verbose_name=_('Foto de perfil')
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
    
    def get_module_permissions(self, module):
        """
        Obtiene los permisos del usuario para un módulo específico
        """
        try:
            module_instance = Module.objects.get(name=module)  # Suponiendo que `Module` tiene un campo `name`
            module_permission = ModulePermission.objects.get(
                module=module_instance,
                user_type=self.user_type
            )
            return {
                'can_view': module_permission.can_view,
                'can_create': module_permission.can_create,
                'can_edit': module_permission.can_edit,
                'can_delete': module_permission.can_delete
            }
        except (Module.DoesNotExist, ModulePermission.DoesNotExist):
            return {
                'can_view': False,
                'can_create': False,
                'can_edit': False,
                'can_delete': False
            }


    def has_module_permission(self, module, permission_type):
        """
        Verifica si el usuario tiene un permiso específico para un módulo
        
        Args:
            module: Instancia del módulo o ID del módulo
            permission_type: String ('view', 'create', 'edit', 'delete')
        """

        if isinstance(module, int):
            module = get_object_or_404(Module, id=module)

        permissions = self.get_module_permissions(module)
        return permissions.get(f'can_{permission_type}', False)

    def log_module_access(self, module, request=None):
        """
        Registra el acceso del usuario a un módulo
        """
        access_log = UserModuleAccess(
            user=self,
            module=module,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT') if request else ''
        )
        access_log.save()

class Module(models.Model):
    """
    Modelo para definir los módulos del sistema académico
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True)
    url = models.CharField(max_length=200)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Módulo')
        verbose_name_plural = _('Módulos')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class ModulePermission(models.Model):
    """
    Modelo para gestionar permisos específicos por módulo y tipo de usuario
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    user_type = models.CharField(max_length=10, choices=User.USER_TYPE_CHOICES)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Permiso de Módulo')
        verbose_name_plural = _('Permisos de Módulos')
        unique_together = ['module', 'user_type']

    def __str__(self):
        return f"{self.module.name} - {self.user_type}"

class UserModuleAccess(models.Model):
    """
    Modelo para registrar y auditar el acceso de usuarios a los módulos
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Acceso a Módulo')
        verbose_name_plural = _('Accesos a Módulos')