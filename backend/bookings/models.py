from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Availability(models.Model):
    """Disponibilités des avocats"""
    
    STATUS_CHOICES = (
        ('free', 'Libre'),
        ('booked', 'Réservé'),
    )
    
    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'role': 'lawyer'}
    )
    start_time = models.DateTimeField(verbose_name="Début")
    end_time = models.DateTimeField(verbose_name="Fin")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Disponibilité"
        verbose_name_plural = "Disponibilités"
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['lawyer', 'start_time']),
            models.Index(fields=['start_time', 'status']),
        ]
    
    def __str__(self):
        return f"{self.lawyer.email} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duration_minutes(self):
        """Durée en minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        
        # Vérifier que start_time < end_time
        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être avant l'heure de fin")
        
        # Vérifier que la durée ne dépasse pas 4 heures
        if self.duration_minutes > 240:
            raise ValidationError("La durée ne peut pas dépasser 4 heures")
        
        # Vérifier que start_time n'est pas dans le passé
        if self.start_time < timezone.now():
            raise ValidationError("Impossible de créer une disponibilité dans le passé")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Appointment(models.Model):
    """Rendez-vous entre client et avocat"""
    
    STATUS_CHOICES = (
        ('pending', 'En attente de paiement'),
        ('paid', 'Payé'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('missed', 'Absent'),
    )
    
    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lawyer_appointments',
        limit_choices_to={'role': 'lawyer'}
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_appointments',
        limit_choices_to={'role': 'client'}
    )
    availability = models.OneToOneField(
        Availability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointment'
    )
    start_time = models.DateTimeField(verbose_name="Début")
    duration = models.IntegerField(default=60, verbose_name="Durée (minutes)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    video_room_url = models.URLField(blank=True, null=True, verbose_name="Lien visio")
    client_notes = models.TextField(blank=True, max_length=500, verbose_name="Notes client")
    cancellation_reason = models.TextField(blank=True, max_length=500, verbose_name="Raison annulation")
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['lawyer', 'status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['start_time', 'status']),
        ]
    
    def __str__(self):
        return f"{self.client.email} → {self.lawyer.email} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def end_time(self):
        """Heure de fin calculée"""
        from datetime import timedelta
        return self.start_time + timedelta(minutes=self.duration)
    
    def can_cancel(self):
        """Vérifie si le rendez-vous peut être annulé (24h avant minimum)"""
        from django.utils import timezone
        hours_before = (self.start_time - timezone.now()).total_seconds() / 3600
        return hours_before >= 24 and self.status not in ['completed', 'cancelled', 'missed']
    
    def cancel(self, reason=None):
        """Annuler le rendez-vous"""
        if self.can_cancel():
            self.status = 'cancelled'
            self.cancellation_reason = reason or "Annulé par le client"
            self.cancelled_at = timezone.now()
            
            # Libérer la disponibilité si elle existe
            if self.availability:
                self.availability.status = 'free'
                self.availability.save()
            
            self.save()
            return True
        return False
    
    def complete(self):
        """Marquer le rendez-vous comme terminé"""
        self.status = 'completed'
        self.save()
    
    def confirm(self):
        """Confirmer le rendez-vous après paiement"""
        self.status = 'confirmed'
        self.save()
        
        # Marquer la disponibilité comme réservée
        if self.availability:
            self.availability.status = 'booked'
            self.availability.save()