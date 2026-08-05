"""
Models base e abstratos do sistema.
Estes models fornecem funcionalidades comuns para todos os outros apps.
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Model abstrato que adiciona campos de data de criação e atualização.
    """
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        editable=False,
        db_index=True
    )
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True,
        editable=False,
        db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Model abstrato que adiciona soft delete (exclusão lógica).
    """
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        db_index=True,
        help_text='Desative para fazer exclusão lógica do registro'
    )
    deleted_at = models.DateTimeField(
        'Excluído em',
        null=True,
        blank=True,
        editable=False
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Realiza soft delete ao invés de exclusão física."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        """Realiza exclusão física do registro."""
        super().delete()


class SlugModel(models.Model):
    """
    Model abstrato que adiciona campo slug para URLs amigáveis.
    """
    slug = models.SlugField(
        'Slug',
        max_length=200,
        unique=True,
        blank=True,
        help_text='URL amigável gerada automaticamente'
    )

    class Meta:
        abstract = True


class OrderModel(models.Model):
    """
    Model abstrato que adiciona campo de ordem para listas ordenadas.
    """
    order = models.PositiveIntegerField(
        'Ordem',
        default=0,
        db_index=True,
        help_text='Ordem de exibição (menor primeiro)'
    )

    class Meta:
        abstract = True
        ordering = ['order', 'created_at']


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Model base completo que combina todas as funcionalidades abstratas.
    Usado quando todos os recursos são necessários.
    """
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseModelWithSlug(BaseModel, SlugModel):
    """
    Model base com slug.
    """
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseModelWithOrder(BaseModel, OrderModel):
    """
    Model base com ordem.
    """
    
    class Meta:
        abstract = True
        ordering = ['order', '-created_at']
