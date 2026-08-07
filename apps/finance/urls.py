from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),
    path('transacoes/', views.TransactionListView.as_view(), name='transactions'),
    path('transacoes/adicionar/', views.TransactionCreateView.as_view(), name='add_transaction'),
    path('transacoes/<int:pk>/', views.TransactionDetailView.as_view(), name='detail'),
    path('transacoes/<int:pk>/editar/', views.TransactionUpdateView.as_view(), name='edit'),
    path('transacoes/<int:pk>/excluir/', views.TransactionDeleteView.as_view(), name='delete'),
    path('caixa/', views.CashRegisterView.as_view(), name='cash_register'),
    path('caixa/abrir/', views.CashRegisterOpenView.as_view(), name='open_cash'),
    path('caixa/fechar/', views.CashRegisterCloseView.as_view(), name='close_cash'),
    path('comissoes/', views.CommissionListView.as_view(), name='commissions'),
    
    # Gastos Fixos
    path('gastos-fixos/', views.FixedExpenseListView.as_view(), name='fixed_expenses'),
    path('gastos-fixos/adicionar/', views.FixedExpenseCreateView.as_view(), name='fixed_expense_add'),
    path('gastos-fixos/<int:pk>/editar/', views.FixedExpenseUpdateView.as_view(), name='fixed_expense_edit'),
    path('gastos-fixos/<int:pk>/excluir/', views.FixedExpenseDeleteView.as_view(), name='fixed_expense_delete'),
    path('gastos-fixos/<int:pk>/cobrar/', views.FixedExpenseChargeView.as_view(), name='fixed_expense_charge'),
    
    # Relatório de Lucro por Barbeiro
    path('lucro-barbeiros/', views.BarberProfitReportView.as_view(), name='barber_profit'),
]
