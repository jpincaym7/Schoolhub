from rest_framework import serializers
from apps.users.models import Module, ModulePermission


class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo de Módulo
    """
    class Meta:
        model = Module
        fields = ['id', 'name', 'code', 'description', 'is_active', 'order', 'icon', 'url', 'parent', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ModulePermissionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo de Permiso de Módulo
    """
    class Meta:
        model = ModulePermission
        fields = ['id', 'module', 'user_type', 'can_view', 'can_create', 'can_edit', 'can_delete', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        # Validación personalizada
        if not data.get('module'):
            raise serializers.ValidationError({"module": "El módulo es requerido"})
        if not data.get('user_type'):
            raise serializers.ValidationError({"user_type": "El tipo de usuario es requerido"})
        
        # Verificar si ya existe un permiso para este tipo de usuario y módulo
        existing = ModulePermission.objects.filter(
            module=data['module'],
            user_type=data['user_type']
        ).exists()
        
        if existing and not self.instance:  # Solo para creación
            raise serializers.ValidationError(
                {"non_field_errors": "Ya existe un permiso para este tipo de usuario en este módulo"}
            )
        
        return data
