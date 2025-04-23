import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bidding_system.settings')

app = Celery('bidding')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()  # Automatically discover tasks from all installed apps
