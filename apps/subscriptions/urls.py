from django.urls import path
from . import views  # ADICIONAR ESTA LINHA

app_name = 'subscriptions'

urlpatterns = [
    path('', views.SubscriptionListView.as_view(), name='list'),
    path('planos/', views.PlanListView.as_view(), name='plans'),
    path('assinar/', views.SubscriptionCreateView.as_view(), name='subscribe'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), name='detail'),
    path('<int:pk>/cancelar/', views.SubscriptionCancelView.as_view(), name='cancel'),
]
