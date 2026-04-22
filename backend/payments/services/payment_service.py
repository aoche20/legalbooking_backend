from payments.models import PaymentMethod, Payment

class PaymentService:
    """Service principal de gestion des paiements"""
    
    @staticmethod
    def get_available_methods(country=None):
        """Récupérer les méthodes actives"""
        queryset = PaymentMethod.objects.filter(is_active=True)
        if country:
            queryset = queryset.filter(countries__contains=[country])
        return queryset
    
    @staticmethod
    def calculate_amount(amount, method_code):
        """Calculer le montant total avec frais"""
        try:
            method = PaymentMethod.objects.get(name=method_code)
            fees = (amount * method.fee_percentage / 100) + float(method.fee_fixed)
            return {
                'original_amount': float(amount),
                'fees': round(fees, 2),
                'total_amount': round(float(amount) + fees, 2),
                'method': method.display_name
            }
        except PaymentMethod.DoesNotExist:
            return {
                'original_amount': float(amount),
                'fees': 0,
                'total_amount': float(amount)
            }