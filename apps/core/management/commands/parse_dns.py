import logging
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from apps.products.models import Category
from apps.prices.tasks import task_parse_category

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает парсинг DNS для указанной категории или всех активных категорий'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--category',
            type=str,
        )
        parser.add_argument(
            '--sync',
            action='store_true',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        category_slug: str | None = options.get('category')
        is_sync: bool = options.get('sync', False)

        if category_slug:
            categories = Category.objects.filter(slug=category_slug, is_active=True)
        else:
            categories = Category.objects.filter(is_active=True)

        if not categories.exists():
            self.stderr.write(self.style.ERROR('Активные категории не найдены'))
            return

        for category in categories:
            self.stdout.write(f'Запуск парсинга: {category.name} ({category.slug})')
            if is_sync:
                task_parse_category(category.id)
            else:
                task_parse_category.delay(category.id)
                self.stdout.write(self.style.SUCCESS('Задача поставлена в очередь'))

        self.stdout.write(self.style.SUCCESS('Готово'))
