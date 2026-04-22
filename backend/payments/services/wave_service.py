import requests
import json
from django.conf import settings

class WaveService:
    """Paiement par Wave"""
    
    @staticmethod
    def create_payment(amount, phone_number, appointment_id):
        transaction_ref = f"WAVE_{appointment_id}"
        
        payload = {
            'amount': amount,
            'currency': 'XOF',
            'phone_number': phone_number,
            'reference': transaction_ref,
            'webhook': f'{settings.SITE_URL}/api/payments/wave/webhook/'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.WAVE_API_KEY}'
        }
        
        # Simulation
        return {
            'success': True,
            'transaction_id': transaction_ref,
            'checkout_url': f"https://wave.com/pay/{transaction_ref}",
            'qr_code': f"https://wave.com/qr/{transaction_ref}"
        }