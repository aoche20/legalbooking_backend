from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
import json

from .models import Payment, PaymentMethod
from .serializers import (
    PaymentSerializer, PaymentMethodSerializer,
    InitiatePaymentSerializer, VerifyPaymentSerializer
)
from .services import (
    PaymentService, StripeService, MobileMoneyService,
    WaveService, CeltisService, PayPalService
)
from bookings.models import Appointment


class PaymentMethodListView(generics.ListAPIView):
    """Liste des méthodes de paiement disponibles"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentMethodSerializer
    
    def get_queryset(self):
        country = self.request.query_params.get('country')
        return PaymentService.get_available_methods(country)


class InitiatePaymentView(APIView):
    """Initier un paiement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        appointment_id = serializer.validated_data['appointment_id']
        method = serializer.validated_data['payment_method']
        phone_number = serializer.validated_data.get('phone_number')
        
        # Récupérer le rendez-vous
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            client=request.user,
            status='pending'
        )
        
        # Calculer le montant avec frais
        amount = float(appointment.amount)
        fee_info = PaymentService.calculate_amount(amount, method)
        
        # Créer le paiement selon la méthode
        result = None
        
        if method == 'card':
            result = StripeService.create_payment(fee_info['total_amount'], appointment_id)
            if result['success']:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_method=method,
                    amount=amount,
                    fees=fee_info['fees'],
                    total_amount=fee_info['total_amount'],
                    stripe_payment_intent_id=result['transaction_id'],
                    status='pending'
                )
                return Response({
                    'payment_id': payment.id,
                    'client_secret': result['client_secret'],
                    'payment_method': method
                })
        
        elif method in ['orange_money', 'mtn_money']:
            result = MobileMoneyService.create_payment(
                fee_info['total_amount'], phone_number, method, appointment_id
            )
            if result['success']:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_method=method,
                    amount=amount,
                    fees=fee_info['fees'],
                    total_amount=fee_info['total_amount'],
                    transaction_id=result['transaction_id'],
                    phone_number=phone_number,
                    provider=method,
                    status='pending'
                )
                return Response({
                    'payment_id': payment.id,
                    'transaction_id': result['transaction_id'],
                    'payment_url': result.get('payment_url'),
                    'payment_method': method
                })
        
        elif method == 'wave':
            result = WaveService.create_payment(
                fee_info['total_amount'], phone_number, appointment_id
            )
            if result['success']:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_method=method,
                    amount=amount,
                    fees=fee_info['fees'],
                    total_amount=fee_info['total_amount'],
                    transaction_id=result['transaction_id'],
                    phone_number=phone_number,
                    status='pending'
                )
                return Response({
                    'payment_id': payment.id,
                    'checkout_url': result['checkout_url'],
                    'qr_code': result.get('qr_code'),
                    'payment_method': method
                })
        
        elif method == 'celtis':
            result = CeltisService.create_payment(
                fee_info['total_amount'], phone_number, appointment_id
            )
            if result['success']:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_method=method,
                    amount=amount,
                    fees=fee_info['fees'],
                    total_amount=fee_info['total_amount'],
                    celtis_transaction_ref=result['transaction_ref'],
                    phone_number=phone_number,
                    status='pending'
                )
                return Response({
                    'payment_id': payment.id,
                    'payment_url': result['payment_url'],
                    'qr_code': result.get('qr_code'),
                    'transaction_ref': result['transaction_ref'],
                    'payment_method': method
                })
        
        elif method == 'paypal':
            return_url = request.build_absolute_uri('/api/payments/paypal/execute/')
            cancel_url = request.build_absolute_uri('/api/payments/paypal/cancel/')
            
            result = PayPalService.create_payment(
                fee_info['total_amount'], appointment_id, return_url, cancel_url
            )
            if result['success']:
                payment = Payment.objects.create(
                    appointment=appointment,
                    payment_method=method,
                    amount=amount,
                    fees=fee_info['fees'],
                    total_amount=fee_info['total_amount'],
                    paypal_payment_id=result['payment_id'],
                    status='pending'
                )
                return Response({
                    'payment_id': payment.id,
                    'approval_url': result['approval_url'],
                    'payment_method': method
                })
        
        return Response(
            {'error': result.get('error', 'Échec de l\'initiation')},
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyPaymentView(APIView):
    """Vérifier le statut d'un paiement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id, appointment__client=request.user)
        
        if payment.status == 'succeeded':
            return Response({'status': 'succeeded', 'payment_id': payment.id})
        
        # Vérifier selon la méthode
        if payment.payment_method == 'card' and payment.stripe_payment_intent_id:
            result = StripeService.verify_payment(payment.stripe_payment_intent_id)
            if result.get('status') == 'succeeded':
                payment.mark_succeeded()
        
        elif payment.payment_method in ['orange_money', 'mtn_money'] and payment.transaction_id:
            result = MobileMoneyService.check_status(payment.transaction_id)
            if result.get('status') == 'completed':
                payment.mark_succeeded()
        
        elif payment.payment_method == 'celtis' and payment.celtis_transaction_ref:
            result = CeltisService.verify_payment(payment.celtis_transaction_ref)
            if result.get('status') == 'SUCCESS':
                payment.mark_succeeded()
        
        return Response({
            'status': payment.status,
            'payment_id': payment.id,
            'amount': payment.total_amount
        })


# Webhooks
@csrf_exempt
@require_POST
def celtis_webhook(request):
    """Webhook pour les notifications Celtis"""
    try:
        data = json.loads(request.body)
        result = CeltisService.process_webhook(data)
        
        if result['success']:
            from payments.models import Payment
            payment = Payment.objects.filter(celtis_transaction_ref=result['transaction_ref']).first()
            if payment and result['status'] == 'succeeded':
                payment.mark_succeeded()
                return JsonResponse({'status': 'ok'})
        
        return JsonResponse({'status': 'error'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
def mobile_money_webhook(request):
    """Webhook pour Mobile Money"""
    data = json.loads(request.body)
    transaction_id = data.get('transaction_id')
    status = data.get('status')
    
    from payments.models import Payment
    payment = Payment.objects.filter(transaction_id=transaction_id).first()
    
    if payment and status == 'completed':
        payment.mark_succeeded()
    
    return JsonResponse({'status': 'ok'})


@csrf_exempt
@require_POST
def wave_webhook(request):
    """Webhook pour Wave"""
    data = json.loads(request.body)
    transaction_id = data.get('reference')
    status = data.get('status')
    
    from payments.models import Payment
    payment = Payment.objects.filter(transaction_id=transaction_id).first()
    
    if payment and status == 'completed':
        payment.mark_succeeded()
    
    return JsonResponse({'status': 'ok'})