"""
Modelos do app Accounts.
Gerencia usuários, perfis e autenticação.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.validators import validate_cpf, validate_phone
from apps.core.managers import ActiveManager
from .managers import UserManager  # Importação correta


class User(AbstractUser):
    """
    Modelo customizado de usuário.
    Estende o AbstractUser com campos adicionais para a barbearia.
    """
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        MANAGER = 'manager', 'Gerente'
        BARBER = 'barber', 'Barbeiro'
        RECEPTIONIST = 'receptionist', 'Recepcionista'
        CUSTOMER = 'customer', 'Cliente'
    
    # Campos adicionais
    cpf = models.CharField(
        'CPF',
        max_length=14,
        unique=True,
        validators=[validate_cpf],
        blank=True,
        null=True,
        help_text='CPF do usuário (apenas números)'
    )
    
    phone = models.CharField(
        'Telefone',
        max_length=15,
        validators=[validate_phone],
        blank=True,
        help_text='Telefone com DDD (apenas números)'
    )
    
    birth_date = models.DateField(
        'Data de Nascimento',
        blank=True,
        null=True
    )
    
    user_type = models.CharField(
        'Tipo de Usuário',
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER,
        db_index=True
    )
    
    avatar = models.ImageField(
        'Avatar',
        upload_to='profiles/avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='Imagem de perfil do usuário'
    )
    
    bio = models.TextField(
        'Biografia',
        max_length=500,
        blank=True,
        help_text='Breve descrição sobre o usuário'
    )
    
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        db_index=True,
        help_text='Desative para bloquear o acesso do usuário'
    )
    
    last_activity = models.DateTimeField(
        'Última Atividade',
        blank=True,
        null=True,
        editable=False
    )
    
    # Campos de auditoria (serão preenchidos automaticamente)
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        editable=False
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True,
        editable=False
    )
    
    # Managers
    objects = UserManager()  # Usar o UserManager
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['username', 'is_active']),
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['cpf']),
        ]
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def get_full_name(self):
        """Retorna o nome completo do usuário."""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.first_name or self.username
    
    def get_short_name(self):
        """Retorna o primeiro nome."""
        return self.first_name or self.username
    
    def update_last_activity(self):
        """Atualiza o timestamp da última atividade."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN or self.is_superuser
    
    @property
    def is_manager(self):
        return self.user_type == self.UserType.MANAGER
    
    @property
    def is_barber(self):
        return self.user_type == self.UserType.BARBER
    
    @property
    def is_receptionist(self):
        return self.user_type == self.UserType.RECEPTIONIST
    
    @property
    def is_customer(self):
        return self.user_type == self.UserType.CUSTOMER
    
    @property
    def is_staff_or_above(self):
        """Verifica se o usuário é staff ou superior."""
        return self.is_staff or self.is_superuser
    
    def save(self, *args, **kwargs):
        """Override do save para garantir que o username seja sempre minúsculo."""
        if self.username:
            self.username = self.username.lower()
        
        # Se for superuser ou staff, define como admin
        if self.is_superuser or self.is_staff:
            if self.user_type != self.UserType.ADMIN:
                self.user_type = self.UserType.ADMIN
        
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """
    Perfil complementar do usuário.
    Armazena informações adicionais e preferências.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Usuário')
    )
    
    # Preferências de notificação
    email_notifications = models.BooleanField(
        'Notificações por Email',
        default=True,
        help_text='Receber notificações por email'
    )
    
    sms_notifications = models.BooleanField(
        'Notificações por SMS',
        default=False,
        help_text='Receber notificações por SMS'
    )
    
    whatsapp_notifications = models.BooleanField(
        'Notificações por WhatsApp',
        default=True,
        help_text='Receber notificações por WhatsApp'
    )
    
    # Preferências do sistema
    language = models.CharField(
        'Idioma',
        max_length=10,
        default='pt-br',
        choices=[
            ('pt-br', 'Português (Brasil)'),
            ('en', 'English'),
        ]
    )
    
    theme = models.CharField(
        'Tema',
        max_length=20,
        default='light',
        choices=[
            ('light', 'Claro'),
            ('dark', 'Escuro'),
        ]
    )
    
    # Informações adicionais
    address = models.TextField(
        'Endereço',
        max_length=200,
        blank=True
    )
    
    city = models.CharField(
        'Cidade',
        max_length=100,
        blank=True
    )
    
    state = models.CharField(
        'Estado',
        max_length=2,
        blank=True
    )
    
    zip_code = models.CharField(
        'CEP',
        max_length=10,
        blank=True
    )
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Perfil do Usuário')
        verbose_name_plural = _('Perfis dos Usuários')
    
    def __str__(self):
        return f'Perfil de {self.user.get_full_name()}'
    
    @property
    def full_address(self):
        """Retorna o endereço completo formatado."""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        return ', '.join(parts) if parts else ''
