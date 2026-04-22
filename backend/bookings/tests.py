from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.validators import ValidationError
from users.models import ClientProfile, LawyerProfile

User = get_user_model()

class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def test_create_client_user(self):
        """Test création d'un utilisateur client"""
        user = User.objects.create_user(
            email='client@test.com',
            password='password123',
            first_name='Jean',
            last_name='Dupont',
            role='client'
        )
        
        self.assertEqual(user.email, 'client@test.com')
        self.assertEqual(user.role, 'client')
        self.assertTrue(user.check_password('password123'))
    
    def test_create_lawyer_user(self):
        """Test création d'un utilisateur avocat"""
        user = User.objects.create_user(
            email='lawyer@test.com',
            password='password123',
            first_name='Marie',
            last_name='Martin',
            role='lawyer'
        )
        
        self.assertEqual(user.email, 'lawyer@test.com')
        self.assertEqual(user.role, 'lawyer')
    
    def test_email_is_unique(self):
        """Test que l'email est unique"""
        User.objects.create_user(
            email='test@test.com',
            password='password123',
            role='client'
        )
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@test.com',
                password='password123',
                role='client'
            )


class LawyerProfileModelTest(TestCase):
    """Tests pour le modèle LawyerProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='lawyer@test.com',
            password='password123',
            role='lawyer'
        )
    
    def test_create_lawyer_profile(self):
        """Test création d'un profil avocat"""
        profile = LawyerProfile.objects.create(
            user=self.user,
            bar_number='PARIS123',
            speciality='Droit de la famille',
            hourly_rate=150.00,
            city='Paris'
        )
        
        self.assertEqual(profile.bar_number, 'PARIS123')
        self.assertEqual(float(profile.hourly_rate), 150.00)
        self.assertEqual(profile.rating, 0)
    
    def test_rating_validation(self):
        """Test que la note est entre 0 et 5"""
        profile = LawyerProfile.objects.create(
            user=self.user,
            bar_number='PARIS123',
            speciality='Droit',
            hourly_rate=150,
            city='Paris'
        )
        
        # Note valide
        profile.rating = 4.5
        profile.full_clean()  # Ne doit pas lever d'erreur
        
        # Note invalide (trop élevée)
        profile.rating = 6.0
        with self.assertRaises(ValidationError):
            profile.full_clean()


class AuthAPITestCase(TestCase):
    """Tests pour l'API d'authentification"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_register_client_success(self):
        """Test inscription client réussie"""
        data = {
            'email': 'client@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'role': 'client'
        }
        
        response = self.client.post('/api/users/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], 'client@test.com')
    
    def test_register_lawyer_success(self):
        """Test inscription avocat réussie"""
        data = {
            'email': 'avocat@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'Marie',
            'last_name': 'Martin',
            'role': 'lawyer',
            'bar_number': 'PARIS123',
            'speciality': 'Droit de la famille',
            'hourly_rate': 150.00,
            'city': 'Paris'
        }
        
        response = self.client.post('/api/users/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'lawyer')
    
    def test_login_success(self):
        """Test connexion réussie"""
        # Créer l'utilisateur d'abord
        User.objects.create_user(
            email='test@test.com',
            password='password123',
            role='client'
        )
        
        login_data = {
            'email': 'test@test.com',
            'password': 'password123'
        }
        
        response = self.client.post('/api/users/login/', login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_login_invalid_credentials(self):
        """Test connexion avec identifiants incorrects"""
        login_data = {
            'email': 'wrong@test.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/users/login/', login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_profile_authenticated(self):
        """Test accès au profil avec token"""
        # Créer et récupérer le token
        user = User.objects.create_user(
            email='test@test.com',
            password='password123',
            role='client'
        )
        
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Accéder au profil
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/users/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@test.com')
    
    def test_unauthenticated_access_denied(self):
        """Test accès sans authentification"""
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)