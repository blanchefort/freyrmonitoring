import os  
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freyr_app.settings')
celery_app = Celery('freyr_app')  
celery_app.config_from_object('django.conf:settings', namespace='CELERY')  
celery_app.autodiscover_tasks()  

celery_app.conf.beat_schedule = {
    'sites_article_collector': {
        'task': 'sites_article_collector',  
        'schedule': crontab(minute=0, hour='*/6'),
    },
#     'define_themes': {
#         'task': 'define_themes',  
#         'schedule': crontab(minute=40, hour='*/1'),
#     },
}