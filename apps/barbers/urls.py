from django.urls import path
from . import views

app_name = 'barbers'

urlpatterns = [
    path('', views.BarberListView.as_view(), name='list'),
    path('adicionar/', views.BarberCreateView.as_view(), name='add'),
    path('<int:pk>/', views.BarberDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.BarberUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.BarberDeleteView.as_view(), name='delete'),
    path('horarios/', views.WorkScheduleListView.as_view(), name='schedule_list'),
    path('horarios/adicionar/', views.WorkScheduleCreateView.as_view(), name='schedule_add'),
    path('horarios/<int:pk>/editar/', views.WorkScheduleUpdateView.as_view(), name='schedule_edit'),
    path('horarios/<int:pk>/excluir/', views.WorkScheduleDeleteView.as_view(), name='schedule_delete'),
]
