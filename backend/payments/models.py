from django.db import models
from django.conf import settings

class PaymentMethod(models.Model):
    """Méthodes de paiement disponibles"""
    
    METHOD_CHOICES = (
        ('card', 'Carte bancaire'),
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('wave', 'Wave'),
        ('celtis', 'Celtis Bénin'),
        ('paypal', 'PayPal'),
    )
    
    name = models.CharField(max_length=20, choices=METHOD_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    countries = models.JSONField(default=list, blank=True, help_text="Pays où disponible")
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order']
    
    def __str__(self):
        return self.display_name


class Payment(models.Model):
    """Transaction de paiement"""
    
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('succeeded', 'Réussi'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    )
    
    appointment = models.OneToOneField(
        'bookings.Appointment',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_method = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Identifiants externes
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Mobile Money
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    
    # Celtis spécifique
    celtis_transaction_ref = models.CharField(max_length=100, blank=True, null=True)
    celtis_payment_url = models.URLField(blank=True, null=True)
    
    # Réponses API
    api_request = models.JSONField(default=dict, blank=True)
    api_response = models.JSONField(default=dict, blank=True)
    
    # Métadonnées
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount}€ - {self.status}"
    
    def mark_succeeded(self):
        """Marquer le paiement comme réussi"""
        from django.utils import timezone
        self.status = 'succeeded'
        self.paid_at = timezone.now()
        self.save()
        
        # Mettre à jour le rendez-vous
        appointment = self.appointment
        appointment.status = 'confirmed'
        appointment.save()