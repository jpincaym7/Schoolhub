from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Permission
from apps.users.models import User
from django.contrib.contenttypes.models import ContentType

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('Usuario desactivado.')
            else:
                raise serializers.ValidationError('Credenciales incorrectas.')
        else:
            raise serializers.ValidationError('Debe incluir "username" y "password".')

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone', 'address', 'full_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone', 'address')
        read_only_fields = ('id',)

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            if request.user.user_type != 'admin' and attrs.get('user_type') in ['teacher', 'parent']:
                raise serializers.ValidationError({
                    "user_type": "Solo los administradores pueden crear usuarios de tipo profesor o representante."
                })
        return attrs

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'phone', 'address')
        read_only_fields = ('id',)

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            if request.user.user_type != 'admin' and attrs.get('user_type') in ['teacher', 'parent']:
                raise serializers.ValidationError({
                    "user_type": "Solo los administradores pueden modificar usuarios de tipo profesor o representante."
                })
        return attrs