"""
Views para o app Products.
"""

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Product, ProductCategory, InventoryMovement
from .forms import ProductForm, ProductCategoryForm


class ProductCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    permission_required = 'products.view_productcategory'
    paginate_by = 20


class ProductCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    permission_required = 'products.add_productcategory'
    success_url = reverse_lazy('products:category_list')


class ProductCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    permission_required = 'products.change_productcategory'
    success_url = reverse_lazy('products:category_list')


class ProductCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'products/category_confirm_delete.html'
    permission_required = 'products.delete_productcategory'
    success_url = reverse_lazy('products:category_list')


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    permission_required = 'products.view_product'
    paginate_by = 20


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    permission_required = 'products.add_product'
    success_url = reverse_lazy('products:list')


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    permission_required = 'products.change_product'
    success_url = reverse_lazy('products:list')


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    permission_required = 'products.delete_product'
    success_url = reverse_lazy('products:list')


class ProductDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    permission_required = 'products.view_product'


class InventoryMovementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = InventoryMovement
    template_name = 'products/movement_list.html'
    context_object_name = 'movements'
    permission_required = 'products.view_inventorymovement'
    paginate_by = 30
