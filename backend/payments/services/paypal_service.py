import paypalrestsdk
from django.conf import settings

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

class PayPalService:
    """Paiement par PayPal"""
    
    @staticmethod
    def create_payment(amount, appointment_id, return_url, cancel_url):
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": str(amount), "currency": "EUR"},
                "description": f"Consultation juridique #{appointment_id}",
                "invoice_number": f"LEGAL_{appointment_id}"
            }],
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        })
        
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'approval_url': link.href
                    }
        return {'success': False, 'error': payment.error}
    
    @staticmethod
    def execute_payment(payment_id, payer_id):
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            return {'success': True, 'payment': payment}
        return {'success': False, 'error': payment.error}