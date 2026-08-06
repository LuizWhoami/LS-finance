from django.urls import path
from . import views  # ADICIONAR ESTA LINHA

app_name = 'reports'

urlpatterns = [
    path('', views.ReportDashboardView.as_view(), name='dashboard'),
    path('financeiro/', views.FinancialReportView.as_view(), name='financial'),
    path('agendamentos/', views.AppointmentsReportView.as_view(), name='appointments'),
    path('clientes/', views.CustomersReportView.as_view(), name='customers'),
    path('barbeiros/', views.BarbersReportView.as_view(), name='barbers'),
    path('produtos/', views.ProductsReportView.as_view(), name='products'),
    path('assinaturas/', views.SubscriptionsReportView.as_view(), name='subscriptions'),
]
