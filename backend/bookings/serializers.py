from rest_framework import serializers
from django.utils import timezone
from .models import Availability, Appointment
from users.serializers import UserSerializer

class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer pour les disponibilités"""
    
    lawyer_name = serializers.ReadOnlyField(source='lawyer.get_full_name')
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = Availability
        fields = [
            'id', 'lawyer', 'lawyer_name', 'start_time', 'end_time',
            'status', 'duration_minutes', 'created_at'
        ]
        read_only_fields = ['id', 'lawyer_name', 'duration_minutes', 'created_at']
    
    def validate(self, data):
        """Validation personnalisée"""
        lawyer = data.get('lawyer')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Vérifier les chevauchements
        overlapping = Availability.objects.filter(
            lawyer=lawyer,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status='free'
        )
        
        if self.instance:
            overlapping = overlapping.exclude(id=self.instance.id)
        
        if overlapping.exists():
            raise serializers.ValidationError(
                "Cette disponibilité chevauche une disponibilité existante"
            )
        
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer pour les rendez-vous"""
    
    lawyer_detail = UserSerializer(source='lawyer', read_only=True)
    client_detail = UserSerializer(source='client', read_only=True)
    can_cancel = serializers.ReadOnlyField()
    end_time = serializers.ReadOnlyField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'lawyer', 'lawyer_detail', 'client', 'client_detail',
            'availability', 'start_time', 'end_time', 'duration', 'status',
            'amount', 'video_room_url', 'client_notes', 'can_cancel',
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'video_room_url', 'created_at', 'can_cancel', 'end_time']


class CreateAppointmentSerializer(serializers.ModelSerializer):
    """Serializer pour créer un rendez-vous"""
    
    class Meta:
        model = Appointment
        fields = [
            'lawyer', 'availability', 'start_time', 'duration',
            'amount', 'stripe_payment_intent_id', 'client_notes'
        ]
    
    def validate(self, data):
        """Validation avant création"""
        start_time = data.get('start_time')
        
        # Vérifier que le créneau n'est pas dans le passé
        if start_time < timezone.now():
            raise serializers.ValidationError(
                "Impossible de réserver un créneau passé"
            )
        
        # Vérifier que le créneau est disponible
        availability = data.get('availability')
        if availability and availability.status != 'free':
            raise serializers.ValidationError(
                "Ce créneau n'est plus disponible"
            )
        
        return data
    
    def create(self, validated_data):
        """Création avec statut initial 'pending'"""
        validated_data['status'] = 'pending'
        return super().create(validated_data)