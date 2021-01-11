"""Команда скачивания новых версий ML-моделей

$python manage.py download_models
"""
import os
import 
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Команда скачивания новых версий ML-моделей'

    def handle(self, *args, **kwargs):
        os.makedirs(settings.AUDIO_PATH, exist_ok=True)
        os.makedirs(settings.CLUSTERS_PATH, exist_ok=True)
        os.makedirs(settings.KALDI, exist_ok=True)