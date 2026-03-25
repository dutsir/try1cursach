import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('price_monitor')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'parse-all-categories-every-6h': {
        'task': 'apps.prices.tasks.task_parse_all_categories',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'check-subscriptions-hourly': {
        'task': 'apps.alerts.tasks.task_check_subscriptions',
        'schedule': crontab(minute=0),
    },
    'detect-anomalies-daily': {
        'task': 'apps.analytics.tasks.task_detect_all_anomalies',
        'schedule': crontab(minute=0, hour=3),
    },
}
