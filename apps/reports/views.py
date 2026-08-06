"""
Views para o app Reports.
"""

from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _

from .models import ReportTemplate, ReportExecution


class ReportDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/dashboard.html'
    permission_required = 'reports.view_reporttemplate'


class FinancialReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/financial.html'
    permission_required = 'reports.view_reporttemplate'


class AppointmentsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/appointments.html'
    permission_required = 'reports.view_reporttemplate'


class CustomersReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/customers.html'
    permission_required = 'reports.view_reporttemplate'


class BarbersReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/barbers.html'
    permission_required = 'reports.view_reporttemplate'


class ProductsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/products.html'
    permission_required = 'reports.view_reporttemplate'


class SubscriptionsReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/subscriptions.html'
    permission_required = 'reports.view_reporttemplate'
