from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """View da página inicial do sistema."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'
        return context


class AboutView(TemplateView):
    """View da página Sobre."""
    template_name = 'core/about.html'
