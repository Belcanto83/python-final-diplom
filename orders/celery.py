import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')

app = Celery('orders')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.event_serializer = 'pickle'
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['application/json', 'application/x-python-serialize']

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# # Celery scheduled tasks
# app.conf.beat_schedule = {
#     'check_mailings_every_1_minutes': {
#         'task': 'backend.tasks.periodic_task',
#         'schedule': crontab(minute='*/1'),
#     },
#     'send_email_every_5_minutes': {
#         'task': 'backend.tasks.send_periodic_email',
#         'schedule': crontab(minute='*/5'),
#     },
# }
