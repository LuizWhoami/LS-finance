"""
Views para o app Services.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import AdminRequiredMixin
from .models import ServiceCategory, Service
from .forms import ServiceCategoryForm, ServiceForm


class ServiceCategoryListView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ServiceCategory
    template_name = 'services/category_list.html'
    context_object_name = 'categories'
    permission_required = 'services.view_servicecategory'
    paginate_by = 20


class ServiceCategoryCreateView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'services/category_form.html'
    permission_required = 'services.add_servicecategory'
    success_url = reverse_lazy('services:category_list')

    def form_valid(self, form):
        messages.success(self.request, _('Categoria criada com sucesso!'))
        return super().form_valid(form)


class ServiceCategoryUpdateView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'services/category_form.html'
    permission_required = 'services.change_servicecategory'
    success_url = reverse_lazy('services:category_list')

    def form_valid(self, form):
        messages.success(self.request, _('Categoria atualizada com sucesso!'))
        return super().form_valid(form)


class ServiceCategoryDeleteView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ServiceCategory
    template_name = 'services/category_confirm_delete.html'
    permission_required = 'services.delete_servicecategory'
    success_url = reverse_lazy('services:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Categoria removida com sucesso!'))
        return super().delete(request, *args, **kwargs)


class ServiceListView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    permission_required = 'services.view_service'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.filter(is_active=True)
        return context


class ServiceCreateView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    permission_required = 'services.add_service'
    success_url = reverse_lazy('services:list')

    def form_valid(self, form):
        messages.success(self.request, _('Serviço criado com sucesso!'))
        return super().form_valid(form)


class ServiceUpdateView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    permission_required = 'services.change_service'
    success_url = reverse_lazy('services:list')

    def form_valid(self, form):
        messages.success(self.request, _('Serviço atualizado com sucesso!'))
        return super().form_valid(form)


class ServiceDeleteView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    permission_required = 'services.delete_service'
    success_url = reverse_lazy('services:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Serviço removido com sucesso!'))
        return super().delete(request, *args, **kwargs)


class ServiceDetailView(AdminRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    permission_required = 'services.view_service'
