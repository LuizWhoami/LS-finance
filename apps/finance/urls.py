from django.urls import path
from . import views  # ADICIONAR ESTA LINHA

app_name = 'finance'

urlpatterns = [
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),
    path('transacoes/', views.TransactionListView.as_view(), name='transactions'),
    path('transacoes/adicionar/', views.TransactionCreateView.as_view(), name='add_transaction'),
    path('caixa/', views.CashRegisterView.as_view(), name='cash_register'),
    path('caixa/abrir/', views.CashRegisterOpenView.as_view(), name='open_cash'),
    path('caixa/fechar/', views.CashRegisterCloseView.as_view(), name='close_cash'),
    path('comissoes/', views.CommissionListView.as_view(), name='commissions'),
]
