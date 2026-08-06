from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel, BaseModelWithOrder, BaseModelWithSlug
from apps.core.validators import validate_percentage, validate_positive
from apps.core.utils import generate_unique_slug


class ServiceCategory(BaseModelWithOrder):
    name = models.CharField(
        _('Nome'),
        max_length=100,
        unique=True,
        db_index=True
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=200,
        blank=True
    )
    
    icon = models.CharField(
        _('Ícone'),
        max_length=50,
        blank=True,
        help_text='Classe do ícone (ex: fas fa-cut)'
    )
    
    color = models.CharField(
        _('Cor'),
        max_length=7,
        default='#0d6efd',
        help_text='Cor em hexadecimal (ex: #0d6efd)'
    )
    
    class Meta:
        verbose_name = _('Categoria de Serviço')
        verbose_name_plural = _('Categorias de Serviços')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Service(BaseModelWithSlug, BaseModelWithOrder):
    
    class ServiceStatus(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        INACTIVE = 'inactive', 'Inativo'
        DISCONTINUED = 'discontinued', 'Descontinuado'
    
    name = models.CharField(
        _('Nome'),
        max_length=100,
        db_index=True
    )
    
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='services',
        verbose_name=_('Categoria')
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=500,
        blank=True,
        help_text='Descrição detalhada do serviço'
    )
    
    price = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Preço do serviço'
    )
    
    duration_minutes = models.PositiveIntegerField(
        _('Duração (minutos)'),
        default=30,
        validators=[MinValueValidator(5)],
        help_text='Tempo estimado para realização do serviço'
    )
    
    commission_percentage = models.DecimalField(
        _('Percentual de Comissão'),
        max_digits=5,
        decimal_places=2,
        default=30.00,
        validators=[validate_percentage],
        help_text='Percentual de comissão para o barbeiro'
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.ACTIVE,
        db_index=True
    )
    
    image = models.ImageField(
        _('Imagem'),
        upload_to='services/%Y/%m/',
        blank=True,
        null=True,
        help_text='Imagem ilustrativa do serviço'
    )
    
    # Comentado temporariamente - será implementado no módulo de produtos
    required_products = models.ManyToManyField(
        'products.Product',
        blank=True,
        through='services.ServiceProduct',
        related_name='services_using_product',
        verbose_name=_('Produtos Necessários')
    )
    
    total_performed = models.PositiveIntegerField(
        _('Total Realizado'),
        default=0,
        help_text='Número total de vezes que este serviço foi realizado'
    )
    
    class Meta:
        verbose_name = _('Serviço')
        verbose_name_plural = _('Serviços')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['name', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Service,
                self.name,
                slug_field='slug',
                max_length=200
            )
        super().save(*args, **kwargs)
    
    @property
    def price_formatted(self):
        from apps.core.utils import format_currency
        return format_currency(self.price)
    
    @property
    def duration_hours(self):
        return self.duration_minutes / 60
    
    @property
    def duration_formatted(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f'{hours}h{minutes}min'
        elif hours > 0:
            return f'{hours}h'
        else:
            return f'{minutes}min'
    
    def increment_performed(self):
        self.total_performed += 1
        self.save(update_fields=['total_performed'])


# Comentado temporariamente - será implementado no módulo de produtos
class ServiceProduct(BaseModel):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='service_products',
        verbose_name=_('Serviço')
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='product_services',
        verbose_name=_('Produto')
    )
    
    quantity = models.DecimalField(
        _('Quantidade'),
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        help_text='Quantidade do produto necessária por serviço'
    )
    
    class Meta:
        verbose_name = _('Produto do Serviço')
        verbose_name_plural = _('Produtos dos Serviços')
        unique_together = [['service', 'product']]
        ordering = ['service', 'product']
    
    def __str__(self):
        return f'{self.service} - {self.product} ({self.quantity})'
