from django.db import models

from apps.core.models import BaseModel
from apps.products.models import Product


class PriceHistory(BaseModel):
    class Source(models.TextChoices):
        DNS = 'dns', 'DNS'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name='Товар',
    )
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    old_price = models.DecimalField(
        'Старая цена (до скидки)', max_digits=12, decimal_places=2, null=True, blank=True,
    )
    timestamp = models.DateTimeField('Время фиксации', db_index=True)
    is_actual = models.BooleanField('Актуальна', default=True)
    source = models.CharField(
        'Источник', max_length=50, choices=Source.choices, default=Source.DNS,
    )

    class Meta:
        verbose_name = 'Запись цены'
        verbose_name_plural = 'История цен'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['product', '-timestamp']),
        ]

    def __str__(self) -> str:
        return f'{self.product.name}: {self.price}₽ ({self.timestamp:%d.%m.%Y %H:%M})'
