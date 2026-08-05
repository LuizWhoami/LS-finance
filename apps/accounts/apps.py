from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Contas e Autenticação'

"""
Configuração do app Accounts.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = _('Contas e Autenticação')
    
    def ready(self):
        """
        Importa os signals quando o app está pronto.
        """
        import apps.accounts.signals
