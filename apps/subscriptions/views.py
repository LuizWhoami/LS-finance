"""
Views para o app Subscriptions.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from decimal import Decimal

from .models import Plan, Subscription


class PlanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Plan
    template_name = 'subscriptions/plan_list.html'
    context_object_name = 'plans'
    permission_required = 'subscriptions.view_plan'
    paginate_by = 20


class PlanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Plan
    fields = ['name', 'description', 'billing_cycle', 'price', 'setup_fee', 
              'discount_percentage', 'free_services_per_month', 'priority_booking', 'status']
    template_name = 'subscriptions/plan_form.html'
    permission_required = 'subscriptions.add_plan'
    success_url = reverse_lazy('subscriptions:plans')


class PlanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Plan
    fields = ['name', 'description', 'billing_cycle', 'price', 'setup_fee', 
              'discount_percentage', 'free_services_per_month', 'priority_booking', 'status']
    template_name = 'subscriptions/plan_form.html'
    permission_required = 'subscriptions.change_plan'
    success_url = reverse_lazy('subscriptions:plans')


class PlanDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Plan
    template_name = 'subscriptions/plan_confirm_delete.html'
    permission_required = 'subscriptions.delete_plan'
    success_url = reverse_lazy('subscriptions:plans')


class SubscriptionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Subscription
    template_name = 'subscriptions/subscription_list.html'
    context_object_name = 'subscriptions'
    permission_required = 'subscriptions.view_subscription'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('customer', 'plan')
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        plan = self.request.GET.get('plan')
        if plan:
            queryset = queryset.filter(plan_id=plan)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(customer__full_name__icontains=search)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Subscription.SubscriptionStatus.choices
        context['plans'] = Plan.objects.filter(is_active=True, status='active')
        return context


class SubscriptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subscription
    fields = ['customer', 'plan', 'start_date', 'end_date', 'next_billing_date', 'payment_method', 'auto_renew', 'notes']
    template_name = 'subscriptions/subscription_form.html'
    permission_required = 'subscriptions.add_subscription'
    success_url = reverse_lazy('subscriptions:list')

    def form_valid(self, form):
        subscription = form.save(commit=False)
        # Preencher campos automaticamente
        subscription.price_paid = subscription.plan.price
        subscription.setup_fee_paid = subscription.plan.setup_fee
        subscription.status = Subscription.SubscriptionStatus.PENDING
        subscription.save()
        
        messages.success(self.request, _('Assinatura criada com sucesso!'))
        return super().form_valid(form)


class SubscriptionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Subscription
    template_name = 'subscriptions/subscription_detail.html'
    context_object_name = 'subscription'
    permission_required = 'subscriptions.view_subscription'


class SubscriptionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Subscription
    fields = ['customer', 'plan', 'start_date', 'end_date', 'next_billing_date', 'payment_method', 'auto_renew', 'notes']
    template_name = 'subscriptions/subscription_form.html'
    permission_required = 'subscriptions.change_subscription'
    success_url = reverse_lazy('subscriptions:list')


class SubscriptionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Subscription
    template_name = 'subscriptions/subscription_confirm_delete.html'
    permission_required = 'subscriptions.delete_subscription'
    success_url = reverse_lazy('subscriptions:list')


class QuickStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View para atualização rápida de status da assinatura."""
    permission_required = 'subscriptions.change_subscription'

    def post(self, request, pk, status):
        subscription = get_object_or_404(Subscription, pk=pk)
        
        valid_statuses = [choice[0] for choice in Subscription.SubscriptionStatus.choices]
        if status not in valid_statuses:
            messages.error(request, _('Status inválido.'))
            return redirect('subscriptions:list')
        
        try:
            if status == 'active':
                subscription.activate()
                messages.success(request, _('Assinatura ativada com sucesso!'))
            elif status == 'suspended':
                subscription.suspend('Suspenso pelo administrador')
                messages.success(request, _('Assinatura suspensa com sucesso!'))
            elif status == 'cancelled':
                subscription.cancel('Cancelado pelo administrador')
                messages.success(request, _('Assinatura cancelada com sucesso!'))
            elif status == 'pending':
                subscription.mark_as_pending()
                messages.success(request, _('Assinatura marcada como pendente!'))
            else:
                messages.error(request, _('Ação não disponível para este status.'))
        except Exception as e:
            messages.error(request, f'Erro ao atualizar status: {str(e)}')
        
        return redirect('subscriptions:list')

from django.http import JsonResponse

def get_plan_duration(request, plan_id):
    """API para buscar a duração do plano em meses."""
    try:
        plan = Plan.objects.get(id=plan_id)
        duration_map = {
            'monthly': 1,
            'quarterly': 3,
            'semester': 6,
            'annual': 12
        }
        duration = duration_map.get(plan.billing_cycle, 1)
        return JsonResponse({
            'duration_months': duration,
            'billing_cycle': plan.billing_cycle
        })
    except Plan.DoesNotExist:
        return JsonResponse({'error': 'Plano não encontrado'}, status=404)
