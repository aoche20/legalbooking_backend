from rest_framework import serializers
from .models import Payment, PaymentMethod

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'display_name', 'icon', 'countries']


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display')
    
    class Meta:
        model = Payment
        fields = [
            'id', 'appointment', 'payment_method', 'payment_method_display',
            'amount', 'fees', 'total_amount', 'status', 'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'paid_at', 'created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=[
        'card', 'orange_money', 'mtn_money', 'wave', 'celtis', 'paypal'
    ])
    phone_number = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        method = data['payment_method']
        phone_number = data.get('phone_number')
        
        # Les méthodes mobile nécessitent un numéro de téléphone
        if method in ['orange_money', 'mtn_money', 'wave', 'celtis']:
            if not phone_number:
                raise serializers.ValidationError({
                    'phone_number': 'Le numéro de téléphone est requis pour ce moyen de paiement'
                })
        
        return data


class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()