import requests
import uuid
from django.conf import settings

class MobileMoneyService:
    """Paiement Orange Money / MTN Mobile Money"""
    
    # Configuration par opérateur
    OPERATORS = {
        'orange_money': {
            'name': 'Orange Money',
            'api_url': 'https://api.orange.com/orange_money/web_payment/create',
            'country': 'CI,SN,ML,BF,BJ,NE'
        },
        'mtn_money': {
            'name': 'MTN Mobile Money',
            'api_url': 'https://api.mtn.com/momo/v1/payment/request',
            'country': 'CI,CM,BF,BJ,RW'
        }
    }
    
    @staticmethod
    def create_payment(amount, phone_number, provider, appointment_id):
        transaction_id = f"MM_{appointment_id}_{uuid.uuid4().hex[:8]}"
        
        payload = {
            'amount': str(amount),
            'currency': 'XOF',
            'phone_number': phone_number,
            'transaction_id': transaction_id,
            'description': f'Consultation juridique #{appointment_id}',
            'callback_url': f'{settings.SITE_URL}/api/payments/mobile-money/webhook/'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.MOBILE_MONEY_API_KEY}'
        }
        
        # Simulation pour développement (à remplacer par vrai appel API)
        # response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        # Simulation
        return {
            'success': True,
            'transaction_id': transaction_id,
            'payment_url': f"https://pay.{provider}.com/{transaction_id}",
            'status': 'pending'
        }
    
    @staticmethod
    def check_status(transaction_id):
        """Vérifier le statut du paiement"""
        # Appel API pour vérifier le statut
        return {'success': True, 'status': 'completed'}