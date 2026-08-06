"""
Views para o app Subscriptions.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Plan, Subscription


class PlanListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Plan
    template_name = 'subscriptions/plan_list.html'
    context_object_name = 'plans'
    permission_required = 'subscriptions.view_plan'
    paginate_by = 20


class SubscriptionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Subscription
    template_name = 'subscriptions/subscription_list.html'
    context_object_name = 'subscriptions'
    permission_required = 'subscriptions.view_subscription'
    paginate_by = 20


class SubscriptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subscription
    fields = ['customer', 'plan', 'start_date', 'end_date', 'payment_method', 'auto_renew']
    template_name = 'subscriptions/subscription_form.html'
    permission_required = 'subscriptions.add_subscription'
    success_url = reverse_lazy('subscriptions:list')


class SubscriptionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Subscription
    template_name = 'subscriptions/subscription_detail.html'
    context_object_name = 'subscription'
    permission_required = 'subscriptions.view_subscription'


class SubscriptionCancelView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Subscription
    template_name = 'subscriptions/subscription_cancel.html'
    permission_required = 'subscriptions.change_subscription'

    def post(self, request, *args, **kwargs):
        subscription = self.get_object()
        reason = request.POST.get('reason', '')
        try:
            subscription.cancel(reason)
            messages.success(request, _('Assinatura cancelada com sucesso!'))
        except Exception as e:
            messages.error(request, str(e))
        return redirect('subscriptions:detail', pk=subscription.pk)
