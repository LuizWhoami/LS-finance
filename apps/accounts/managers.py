"""
Managers específicos para o app Accounts.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.managers import BaseManager


class UserManager(BaseUserManager, BaseManager):
    """
    Manager personalizado para o modelo User.
    """
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Cria e salva um usuário comum.
        """
        if not username:
            raise ValueError(_('O nome de usuário é obrigatório.'))
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Cria e salva um superusuário.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')  # Usar string diretamente
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superusuário deve ter is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superusuário deve ter is_superuser=True.'))
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """
        Permite autenticação por username.
        """
        return self.get(username=username)
    
    def active(self):
        """Retorna apenas usuários ativos."""
        return self.filter(is_active=True)
    
    def by_type(self, user_type):
        """Retorna usuários de um tipo específico."""
        return self.filter(user_type=user_type)
    
    def barbers(self):
        """Retorna apenas barbeiros."""
        return self.by_type('barber')  # Usar string diretamente
    
    def customers(self):
        """Retorna apenas clientes."""
        return self.by_type('customer')  # Usar string diretamente
    
    def search(self, query, fields=None):
        """
        Busca por usuários.
        """
        if not query:
            return self.all()
        
        if fields is None:
            fields = ['username__icontains', 'first_name__icontains', 
                     'last_name__icontains', 'email__icontains', 'cpf__icontains']
        
        q_objects = models.Q()
        for field in fields:
            q_objects |= models.Q(**{field: query})
        
        return self.filter(q_objects)
