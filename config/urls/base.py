"""
Configuração principal das URLs do projeto.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('accounts/', include('apps.accounts.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    
    # Core (Home)
    path('', include('apps.core.urls')),
    
    # NOTA: Os apps abaixo serão adicionados nos próximos módulos
    # Quando o app for criado, descomente a linha correspondente
    # path('barbers/', include('apps.barbers.urls')),
    # path('customers/', include('apps.customers.urls')),
    # path('services/', include('apps.services.urls')),
    # path('appointments/', include('apps.appointments.urls')),
    # path('finance/', include('apps.finance.urls')),
    # path('products/', include('apps.products.urls')),
    # path('subscriptions/', include('apps.subscriptions.urls')),
    # path('reports/', include('apps.reports.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
