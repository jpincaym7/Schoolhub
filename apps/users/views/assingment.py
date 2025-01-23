from rest_framework import serializers
from apps.users.models import Module, ModulePermission

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'name', 'code', 'description', 'is_active', 
                 'order', 'icon', 'url', 'parent', 'created_at', 
                 'updated_at']

class ModulePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePermission
        fields = ['module', 'user_type', 'can_view', 'can_create', 
                 'can_edit', 'can_delete']
