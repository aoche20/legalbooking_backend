import requests
import hashlib
import time
import uuid
from django.conf import settings

class CeltisService:
    """Paiement Celtis Bénin"""
    
    API_BASE = settings.CELTIS_API_URL or 'https://api.celtis.bj/v1'
    
    @staticmethod
    def generate_signature(merchant_code, amount, transaction_id, secret):
        """Générer la signature de sécurité"""
        # Algorithme standard Celtis (à adapter selon documentation)
        data = f"{merchant_code}{amount}{transaction_id}{secret}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def create_payment(amount, phone_number, appointment_id):
        """
        Initier un paiement Celtis
        """
        transaction_ref = f"CEL_{appointment_id}_{int(time.time())}"
        
        payload = {
            'merchant_code': settings.CELTIS_MERCHANT_CODE,
            'amount': str(amount),
            'currency': 'XOF',
            'phone_number': phone_number,
            'transaction_id': transaction_ref,
            'description': f'Consultation juridique #{appointment_id}',
            'callback_url': f'{settings.SITE_URL}/api/payments/celtis/webhook/',
            'return_url': f'{settings.SITE_URL}/payment/success',
            'cancel_url': f'{settings.SITE_URL}/payment/cancel'
        }
        
        # Générer la signature
        payload['signature'] = CeltisService.generate_signature(
            payload['merchant_code'],
            payload['amount'],
            payload['transaction_id'],
            settings.CELTIS_API_SECRET
        )
        
        try:
            # Appel API réel (décommenter en production)
            # response = requests.post(
            #     f'{CeltisService.API_BASE}/payment/initiate',
            #     json=payload,
            #     headers={'Content-Type': 'application/json'},
            #     timeout=30
            # )
            # data = response.json()
            
            # Simulation pour développement
            data = {
                'success': True,
                'payment_url': f"https://pay.celtis.bj/{transaction_ref}",
                'transaction_ref': transaction_ref,
                'qr_code': f"https://pay.celtis.bj/qr/{transaction_ref}"
            }
            
            if data.get('success'):
                return {
                    'success': True,
                    'transaction_ref': transaction_ref,
                    'payment_url': data.get('payment_url'),
                    'qr_code': data.get('qr_code')
                }
            else:
                return {'success': False, 'error': data.get('message', 'Erreur Celtis')}
                
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_payment(transaction_ref):
        """Vérifier le statut d'un paiement Celtis"""
        try:
            # response = requests.get(
            #     f'{CeltisService.API_BASE}/payment/status/{transaction_ref}',
            #     headers={'Authorization': f'Bearer {settings.CELTIS_API_SECRET}'}
            # )
            # data = response.json()
            
            # Simulation
            data = {'status': 'SUCCESS', 'amount': 100}
            
            return {
                'success': True,
                'status': data.get('status'),
                'amount': data.get('amount')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def process_webhook(data):
        """
        Traiter la notification webhook de Celtis
        """
        transaction_ref = data.get('transaction_id')
        status = data.get('status')
        signature = data.get('signature')
        
        # Vérifier la signature
        # if not verify_signature(data, signature):
        #     return {'success': False, 'error': 'Invalid signature'}
        
        if status == 'SUCCESS':
            return {
                'success': True,
                'transaction_ref': transaction_ref,
                'status': 'succeeded'
            }
        elif status == 'FAILED':
            return {
                'success': True,
                'transaction_ref': transaction_ref,
                'status': 'failed'
            }
        
        return {'success': False, 'error': 'Unknown status'}