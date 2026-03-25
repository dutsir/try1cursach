from django.db import models

from apps.core.models import BaseModel
from apps.products.models import Product


class Anomaly(BaseModel):
    class Severity(models.TextChoices):
        LOW = 'low', 'Низкая'
        MEDIUM = 'medium', 'Средняя'
        HIGH = 'high', 'Высокая'

    class AnomalyType(models.TextChoices):
        SPIKE = 'spike', 'Резкий скачок'
        MANIPULATION = 'manipulation', 'Манипуляция (подъём перед скидкой)'
        CYCLIC = 'cyclic', 'Циклическое колебание'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name='Товар',
    )
    detected_at = models.DateTimeField('Обнаружена', auto_now_add=True, db_index=True)
    anomaly_type = models.CharField(
        'Тип аномалии', max_length=50, choices=AnomalyType.choices,
    )
    severity = models.CharField(
        'Серьёзность', max_length=20, choices=Severity.choices,
    )
    description = models.TextField('Описание')
    resolved = models.BooleanField('Разрешена', default=False)

    class Meta:
        verbose_name = 'Аномалия'
        verbose_name_plural = 'Аномалии'
        ordering = ['-detected_at']

    def __str__(self) -> str:
        return f'[{self.severity}] {self.product.name} — {self.anomaly_type}'
