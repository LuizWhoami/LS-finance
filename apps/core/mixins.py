"""
Mixins para o app Core.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar se o usuário é admin/staff."""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        return redirect('client:home')
