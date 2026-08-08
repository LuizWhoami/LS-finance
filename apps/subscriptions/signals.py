"""
Signals para o app Subscriptions.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Subscription
from apps.finance.models import Transaction


@receiver(post_save, sender=Subscription)
def create_subscription_transaction(sender, instance, created, **kwargs):
    """Cria uma transação financeira quando uma assinatura é ativada."""
    if instance.status == Subscription.SubscriptionStatus.ACTIVE:
        # Verificar se já existe transação para esta assinatura
        existing_transaction = Transaction.objects.filter(
            description__icontains=f'Assinatura: {instance.plan.name}',
            customer=instance.customer,
            transaction_date__date=timezone.now().date()
        ).exists()
        
        if not existing_transaction:
            Transaction.objects.create(
                customer=instance.customer,
                transaction_type=Transaction.TransactionType.INCOME,
                payment_method=instance.payment_method,
                amount=instance.price_paid,
                description=f'Assinatura: {instance.plan.name} - Cliente: {instance.customer.full_name}',
                transaction_date=timezone.now(),
                reference=f'subscription_{instance.id}'
            )
