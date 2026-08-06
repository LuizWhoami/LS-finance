"""
Forms para o app Finance.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Transaction, CashRegister, Commission
from apps.customers.models import Customer


class TransactionForm(forms.ModelForm):
    """Formulário de transação com campo de nome do cliente."""

    customer_name = forms.CharField(
        label='Nome do Cliente',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome do cliente'
        })
    )
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'payment_method', 'amount',
            'description', 'transaction_date', 'barber',
            'appointment', 'cash_register', 'customer_name'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição da transação'
            }),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'barber': forms.Select(attrs={'class': 'form-select'}),
            'appointment': forms.Select(attrs={'class': 'form-select'}),
            'cash_register': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remover o campo customer do ModelForm (vamos usar customer_name)
        self.fields.pop('customer', None)
        
        # Definir data atual como padrão
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now()
        
        # Filtrar apenas barbeiros ativos
        from apps.barbers.models import Barber
        self.fields['barber'].queryset = Barber.objects.filter(is_active=True)
        self.fields['barber'].required = False
    
    def save(self, commit=True):
        """Salva a transação e cria/vincula cliente se necessário."""
        instance = super().save(commit=False)
        
        customer_name = self.cleaned_data.get('customer_name')
        
        # Se tiver nome do cliente, buscar ou criar
        if customer_name:
            customer, created = Customer.objects.get_or_create(
                full_name=customer_name,
                defaults={
                    'phone': '',
                    'email': '',
                    'status': 'active'
                }
            )
            instance.customer = customer
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class CashRegisterForm(forms.ModelForm):
    """Formulário para abrir caixa."""
    
    class Meta:
        model = CashRegister
        fields = ['opening_balance', 'opened_by', 'notes']
        widgets = {
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'opened_by': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a abertura do caixa'
            }),
        }
