# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db import transaction
from .models import User, ClientProfile, LawyerProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role')
        read_only_fields = ('id', 'role')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['client', 'lawyer'])
    
    # Champs spécifiques client
    birth_date = serializers.DateField(required=False)
    address = serializers.CharField(required=False)
    
    # Champs spécifiques avocat
    bar_number = serializers.CharField(required=False)
    speciality = serializers.CharField(required=False)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    city = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'phone', 'role', 'birth_date', 'address', 'bar_number', 'speciality',
            'hourly_rate', 'city'
        )
    
    def validate(self, data):
        # Vérifier que les mots de passe correspondent
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas"})
        
        # Vérifier que l'email n'existe pas déjà
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Cet email est déjà utilisé"})
        
        # Si c'est un avocat, vérifier les champs obligatoires
        if data['role'] == 'lawyer':
            if not data.get('bar_number'):
                raise serializers.ValidationError({"bar_number": "Le numéro du barreau est obligatoire"})
            if not data.get('speciality'):
                raise serializers.ValidationError({"speciality": "La spécialité est obligatoire"})
            if not data.get('hourly_rate'):
                raise serializers.ValidationError({"hourly_rate": "Le tarif horaire est obligatoire"})
            if not data.get('city'):
                raise serializers.ValidationError({"city": "La ville est obligatoire"})
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Extraire les champs
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        role = validated_data.pop('role')
        
        # Extraire les champs spécifiques
        birth_date = validated_data.pop('birth_date', None)
        address = validated_data.pop('address', None)
        bar_number = validated_data.pop('bar_number', None)
        speciality = validated_data.pop('speciality', None)
        hourly_rate = validated_data.pop('hourly_rate', None)
        city = validated_data.pop('city', None)
        
        # Créer l'utilisateur
        user = User.objects.create_user(**validated_data)
        user.role = role
        user.save()
        
        # Créer le profil selon le rôle
        if role == 'client':
            ClientProfile.objects.create(
                user=user,
                birth_date=birth_date,
                address=address
            )
        elif role == 'lawyer':
            LawyerProfile.objects.create(
                user=user,
                bar_number=bar_number,
                speciality=speciality,
                hourly_rate=hourly_rate,
                city=city
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email ou mot de passe incorrect")
        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé")
        
        data['user'] = user
        return data


class ProfileSerializer(serializers.ModelSerializer):
    # Champs du profil selon le rôle
    birth_date = serializers.DateField(source='client_profile.birth_date', required=False)
    address = serializers.CharField(source='client_profile.address', required=False)
    bar_number = serializers.CharField(source='lawyer_profile.bar_number', required=False)
    speciality = serializers.CharField(source='lawyer_profile.speciality', required=False)
    bio = serializers.CharField(source='lawyer_profile.bio', required=False)
    hourly_rate = serializers.DecimalField(source='lawyer_profile.hourly_rate', max_digits=10, decimal_places=2, required=False)
    city = serializers.CharField(source='lawyer_profile.city', required=False)
    zoom_link = serializers.URLField(source='lawyer_profile.zoom_link', required=False)
    is_verified = serializers.BooleanField(source='lawyer_profile.is_verified', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone', 'role',
            'birth_date', 'address', 'bar_number', 'speciality', 'bio',
            'hourly_rate', 'city', 'zoom_link', 'is_verified'
        )
        read_only_fields = ('id', 'role', 'is_verified')
    
    def update(self, instance, validated_data):
        # Mettre à jour l'utilisateur
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()
        
        # Mettre à jour le profil selon le rôle
        if instance.role == 'client' and hasattr(instance, 'client_profile'):
            client_data = validated_data.get('client_profile', {})
            profile = instance.client_profile
            profile.birth_date = client_data.get('birth_date', profile.birth_date)
            profile.address = client_data.get('address', profile.address)
            profile.save()
            
        elif instance.role == 'lawyer' and hasattr(instance, 'lawyer_profile'):
            lawyer_data = validated_data.get('lawyer_profile', {})
            profile = instance.lawyer_profile
            profile.bar_number = lawyer_data.get('bar_number', profile.bar_number)
            profile.speciality = lawyer_data.get('speciality', profile.speciality)
            profile.bio = lawyer_data.get('bio', profile.bio)
            profile.hourly_rate = lawyer_data.get('hourly_rate', profile.hourly_rate)
            profile.city = lawyer_data.get('city', profile.city)
            profile.zoom_link = lawyer_data.get('zoom_link', profile.zoom_link)
            profile.save()
        
        return instance