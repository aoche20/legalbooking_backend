# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('lawyer', 'Avocat'),
        ('admin', 'Administrateur'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.email} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"


class ClientProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='client_profile'
    )
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, default='fr')
    newsletter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profil client: {self.user.email}"
    
    class Meta:
        verbose_name = "Profil client"
        verbose_name_plural = "Profils clients"


class LawyerProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='lawyer_profile'
    )
    bar_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro du barreau")
    speciality = models.CharField(max_length=200, verbose_name="Spécialité")
    bio = models.TextField(max_length=1000, blank=True, verbose_name="Biographie")
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Tarif horaire (€)"
    )
    city = models.CharField(max_length=100, verbose_name="Ville")
    zoom_link = models.URLField(blank=True, null=True, verbose_name="Lien Zoom")
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)
    stripe_account_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Me {self.user.last_name} - {self.speciality}"
    
    class Meta:
        verbose_name = "Profil avocat"
        verbose_name_plural = "Profils avocats"