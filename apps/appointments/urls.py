from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.AppointmentListView.as_view(), name='list'),
    path('adicionar/', views.AppointmentCreateView.as_view(), name='add'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.AppointmentUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.AppointmentDeleteView.as_view(), name='delete'),
]
