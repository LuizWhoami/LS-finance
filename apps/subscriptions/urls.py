from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.SubscriptionListView.as_view(), name='list'),
    path('planos/', views.PlanListView.as_view(), name='plans'),
    path('adicionar/', views.SubscriptionCreateView.as_view(), name='add'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.SubscriptionUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.SubscriptionDeleteView.as_view(), name='delete'),
    path('<int:pk>/cancelar/', views.SubscriptionCancelView.as_view(), name='cancel'),
]
