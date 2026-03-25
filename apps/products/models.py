from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('Слаг', max_length=255, unique=True)
    dns_category_slug = models.CharField(
        'Slug категории в DNS',
        max_length=255,
        blank=True,
        default='',
    )
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(BaseModel):
    name = models.CharField('Название', max_length=512)
    slug = models.SlugField('Слаг', max_length=512, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория',
    )
    vendor_code = models.CharField(
        'Артикул', max_length=100, blank=True, default='', db_index=True,
    )
    url = models.URLField('URL на DNS', max_length=1024)
    image_url = models.URLField('URL изображения', max_length=1024, blank=True, default='')
    is_active = models.BooleanField('Активен', default=True)
    last_parsed_at = models.DateTimeField('Последний парсинг', null=True, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-last_parsed_at']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)[:480]
            self.slug = f'{base}-{self.vendor_code}' if self.vendor_code else base
        super().save(*args, **kwargs)
