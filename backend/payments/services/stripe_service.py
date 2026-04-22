import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Paiement par carte bancaire"""
    
    @staticmethod
    def create_payment(amount, appointment_id, currency='eur'):
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency,
                metadata={'appointment_id': appointment_id},
                automatic_payment_methods={'enabled': True}
            )
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'transaction_id': payment_intent.id
            }
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_payment(payment_intent_id):
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100
            }
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}