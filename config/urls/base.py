"""
Configuração principal das URLs do projeto.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Redirecionamento da raiz para o cliente
    path('', RedirectView.as_view(url='/cliente/', permanent=False), name='root'),
    
    # Autenticação
    path('accounts/', include('apps.accounts.urls')),  # Usar apenas accounts
    path('auth/', include('django.contrib.auth.urls')),  # Mantido para compatibilidade
    
    # Admin (Área Administrativa)
    path('dashboard/', include('apps.core.urls')),
    path('services/', include('apps.services.urls')),
    path('customers/', include('apps.customers.urls')),
    path('barbers/', include('apps.barbers.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('products/', include('apps.products.urls')),
    path('finance/', include('apps.finance.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('reports/', include('apps.reports.urls')),
    path('notifications/', include('apps.notifications.urls')),
    
    # Cliente (Área Pública)
    path('cliente/', include('apps.client.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
