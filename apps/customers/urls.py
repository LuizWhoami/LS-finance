from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='list'),
    path('adicionar/', views.CustomerCreateView.as_view(), name='add'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.CustomerUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.CustomerDeleteView.as_view(), name='delete'),
    path('<int:customer_id>/historico/', views.CustomerHistoryView.as_view(), name='history'),
]
