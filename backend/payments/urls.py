from django.urls import path
from .views import (
    PaymentMethodListView, InitiatePaymentView, VerifyPaymentView,
    celtis_webhook, mobile_money_webhook, wave_webhook
)

urlpatterns = [
    # API endpoints
    path('methods/', PaymentMethodListView.as_view(), name='payment-methods'),
    path('initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('verify/<int:payment_id>/', VerifyPaymentView.as_view(), name='verify-payment'),
    
    # Webhooks
    path('celtis/webhook/', celtis_webhook, name='celtis-webhook'),
    path('mobile-money/webhook/', mobile_money_webhook, name='mobile-money-webhook'),
    path('wave/webhook/', wave_webhook, name='wave-webhook'),
]