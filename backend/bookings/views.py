from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Availability, Appointment
from .serializers import (
    AvailabilitySerializer, AppointmentSerializer,
    CreateAppointmentSerializer
)

class AvailabilityListView(generics.ListCreateAPIView):
    """Liste et création des disponibilités"""
    serializer_class = AvailabilitySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Availability.objects.filter(status='free', start_time__gte=timezone.now())
        
        # Filtrer par avocat
        lawyer_id = self.request.query_params.get('lawyer_id')
        if lawyer_id:
            queryset = queryset.filter(lawyer_id=lawyer_id)
        
        # Filtrer par date
        date = self.request.query_params.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                start = timezone.make_aware(date_obj)
                end = start + timedelta(days=1)
                queryset = queryset.filter(start_time__gte=start, start_time__lt=end)
            except ValueError:
                pass
        
        return queryset.order_by('start_time')
    
    def perform_create(self, serializer):
        serializer.save(lawyer=self.request.user)


class AvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification, suppression d'une disponibilité"""
    serializer_class = AvailabilitySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Availability.objects.filter(lawyer=self.request.user)
        return Availability.objects.none()
    
    def get_object(self):
        obj = get_object_or_404(Availability, id=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj


class AppointmentListView(generics.ListCreateAPIView):
    """Liste des rendez-vous et création"""
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAppointmentSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'lawyer':
            queryset = Appointment.objects.filter(lawyer=user)
        elif user.role == 'client':
            queryset = Appointment.objects.filter(client=user)
        else:
            queryset = Appointment.objects.all()
        
        # Filtrer par statut
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrer par date
        date = self.request.query_params.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                start = timezone.make_aware(date_obj)
                end = start + timedelta(days=1)
                queryset = queryset.filter(start_time__gte=start, start_time__lt=end)
            except ValueError:
                pass
        
        return queryset.order_by('-start_time')
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification, annulation d'un rendez-vous"""
    serializer_class = AppointmentSerializer
    
    def get_permissions(self):
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'lawyer':
            return Appointment.objects.filter(lawyer=user)
        elif user.role == 'client':
            return Appointment.objects.filter(client=user)
        return Appointment.objects.all()
    
    def perform_destroy(self, instance):
        """Annulation au lieu de suppression"""
        if instance.can_cancel():
            instance.cancel()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Impossible d'annuler ce rendez-vous (délai dépassé)")


class UpcomingAppointmentsView(APIView):
    """Rendez-vous à venir"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role == 'lawyer':
            appointments = Appointment.objects.filter(
                lawyer=user,
                start_time__gte=timezone.now(),
                status__in=['confirmed', 'paid']
            ).order_by('start_time')[:10]
        else:
            appointments = Appointment.objects.filter(
                client=user,
                start_time__gte=timezone.now(),
                status__in=['confirmed', 'paid']
            ).order_by('start_time')[:10]
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class LawyerAvailableSlotsView(APIView):
    """Créneaux disponibles d'un avocat pour une date"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, lawyer_id, date):
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start = timezone.make_aware(date_obj)
            end = start + timedelta(days=1)
        except ValueError:
            return Response(
                {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availabilities = Availability.objects.filter(
            lawyer_id=lawyer_id,
            start_time__gte=start,
            start_time__lt=end,
            status='free'
        ).order_by('start_time')
        
        serializer = AvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data)