from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Planos
    path('planos/', views.PlanListView.as_view(), name='plans'),
    path('planos/adicionar/', views.PlanCreateView.as_view(), name='plan_create'),
    path('planos/<int:pk>/editar/', views.PlanUpdateView.as_view(), name='plan_edit'),
    path('planos/<int:pk>/excluir/', views.PlanDeleteView.as_view(), name='plan_delete'),
    
    # Assinaturas
    path('', views.SubscriptionListView.as_view(), name='list'),
    path('adicionar/', views.SubscriptionCreateView.as_view(), name='add'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.SubscriptionUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.SubscriptionDeleteView.as_view(), name='delete'),
    
    # Ação rápida de status
    path('quick-status/<int:pk>/<str:status>/', views.QuickStatusUpdateView.as_view(), name='quick_status'),
    
    # API para duração do plano
    path('api/plan-duration/<int:plan_id>/', views.get_plan_duration, name='plan_duration'),
]
