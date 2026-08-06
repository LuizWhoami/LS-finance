"""
Modelos do app Products.
Gerencia produtos e estoque da barbearia.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel, BaseModelWithOrder
from apps.core.validators import validate_positive
from apps.core.exceptions import InsufficientStockError


class ProductCategory(BaseModelWithOrder):
    """
    Categoria de produtos.
    """
    
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
    
    class Meta:
        verbose_name = _('Categoria de Produto')
        verbose_name_plural = _('Categorias de Produtos')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Product(BaseModel):
    """
    Modelo que representa um produto.
    """
    
    class UnitType(models.TextChoices):
        UNIT = 'unit', 'Unidade'
        GRAM = 'g', 'Grama'
        KILOGRAM = 'kg', 'Quilograma'
        MILLILITER = 'ml', 'Mililitro'
        LITER = 'l', 'Litro'
        PACK = 'pack', 'Pacote'
        BOX = 'box', 'Caixa'
    
    # Informações básicas
    name = models.CharField(
        _('Nome'),
        max_length=150,
        db_index=True
    )
    
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Categoria')
    )
    
    description = models.TextField(
        _('Descrição'),
        max_length=500,
        blank=True
    )
    
    # Unidade e quantidade
    unit = models.CharField(
        _('Unidade de Medida'),
        max_length=20,
        choices=UnitType.choices,
        default=UnitType.UNIT
    )
    
    quantity = models.DecimalField(
        _('Quantidade em Estoque'),
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Quantidade atual em estoque'
    )
    
    minimum_stock = models.DecimalField(
        _('Estoque Mínimo'),
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Quantidade mínima para alerta de estoque'
    )
    
    # Valores
    cost_price = models.DecimalField(
        _('Preço de Custo'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Preço de compra do produto'
    )
    
    sale_price = models.DecimalField(
        _('Preço de Venda'),
        max_digits=10,
        decimal_places=2,
        validators=[validate_positive],
        help_text='Preço de venda do produto'
    )
    
    # Status
    is_active = models.BooleanField(
        _('Ativo'),
        default=True,
        db_index=True
    )
    
    # Imagem
    image = models.ImageField(
        _('Imagem'),
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        help_text='Imagem do produto'
    )
    
    class Meta:
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.quantity} {self.get_unit_display()})'
    
    def add_stock(self, quantity, reason, user=None):
        """
        Adiciona estoque do produto.
        """
        if quantity <= 0:
            raise ValidationError(_('A quantidade deve ser positiva.'))
        
        self.quantity += quantity
        self.save(update_fields=['quantity'])
        
        # Registrar movimentação
        InventoryMovement.objects.create(
            product=self,
            movement_type=InventoryMovement.MovementType.IN,
            quantity=quantity,
            previous_quantity=self.quantity - quantity,
            new_quantity=self.quantity,
            reason=reason,
            performed_by=user
        )
    
    def remove_stock(self, quantity, reason, user=None):
        """
        Remove estoque do produto.
        """
        if quantity <= 0:
            raise ValidationError(_('A quantidade deve ser positiva.'))
        
        if self.quantity < quantity:
            raise InsufficientStockError(
                _('Estoque insuficiente. Disponível: {}').format(self.quantity)
            )
        
        previous = self.quantity
        self.quantity -= quantity
        self.save(update_fields=['quantity'])
        
        # Registrar movimentação
        InventoryMovement.objects.create(
            product=self,
            movement_type=InventoryMovement.MovementType.OUT,
            quantity=quantity,
            previous_quantity=previous,
            new_quantity=self.quantity,
            reason=reason,
            performed_by=user
        )
    
    @property
    def is_low_stock(self):
        """Verifica se o estoque está abaixo do mínimo."""
        return self.quantity <= self.minimum_stock
    
    @property
    def profit_margin(self):
        """Retorna a margem de lucro."""
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0


class InventoryMovement(BaseModel):
    """
    Movimentação de estoque.
    """
    
    class MovementType(models.TextChoices):
        IN = 'in', 'Entrada'
        OUT = 'out', 'Saída'
        ADJUSTMENT = 'adjustment', 'Ajuste'
        LOSS = 'loss', 'Perda'
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name=_('Produto')
    )
    
    movement_type = models.CharField(
        _('Tipo de Movimentação'),
        max_length=20,
        choices=MovementType.choices,
        db_index=True
    )
    
    quantity = models.DecimalField(
        _('Quantidade'),
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)]
    )
    
    previous_quantity = models.DecimalField(
        _('Quantidade Anterior'),
        max_digits=10,
        decimal_places=3
    )
    
    new_quantity = models.DecimalField(
        _('Nova Quantidade'),
        max_digits=10,
        decimal_places=3
    )
    
    reason = models.CharField(
        _('Motivo'),
        max_length=200,
        help_text='Motivo da movimentação'
    )
    
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
        verbose_name=_('Realizado por')
    )
    
    class Meta:
        verbose_name = _('Movimentação de Estoque')
        verbose_name_plural = _('Movimentações de Estoque')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'movement_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.product} - {self.get_movement_type_display()} ({self.quantity})'
