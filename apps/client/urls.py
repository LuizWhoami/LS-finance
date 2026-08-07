from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'client'

urlpatterns = [
    path('', views.ClientHomeView.as_view(), name='home'),
    path('servicos/', views.ClientServiceListView.as_view(), name='services'),
    path('barbeiros/', views.ClientBarberListView.as_view(), name='barbers'),
    path('agendar/', views.ClientAppointmentCreateView.as_view(), name='appointment_create'),
    path('agendamentos/', views.ClientAppointmentListView.as_view(), name='appointments'),
    path('agendamentos/<int:pk>/cancelar/', views.ClientAppointmentCancelView.as_view(), name='appointment_cancel'),
    path('perfil/', views.ClientProfileView.as_view(), name='profile'),
    path('login/', views.ClientLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='client:home'), name='logout'),
    path('cadastro/', views.ClientRegisterView.as_view(), name='register'),
    # API para horários disponíveis
    path('api/available-slots/', views.get_available_slots, name='api_available_slots'),
]
