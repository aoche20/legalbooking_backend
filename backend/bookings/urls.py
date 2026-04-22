from django.urls import path
from .views import (
    AvailabilityListView, AvailabilityDetailView,
    AppointmentListView, AppointmentDetailView,
    UpcomingAppointmentsView, LawyerAvailableSlotsView
)

urlpatterns = [
    # Disponibilités
    path('availabilities/', AvailabilityListView.as_view(), name='availability-list'),
    path('availabilities/<int:pk>/', AvailabilityDetailView.as_view(), name='availability-detail'),
    
    # Rendez-vous
    path('appointments/', AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Utilitaires
    path('upcoming/', UpcomingAppointmentsView.as_view(), name='upcoming-appointments'),
    path('lawyers/<int:lawyer_id>/slots/<str:date>/', 
         LawyerAvailableSlotsView.as_view(), name='lawyer-slots'),
]