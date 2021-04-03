"""Команда скачивания новых версий ML-моделей

$python manage.py download_models --full
"""
import logging
from django.core.management.base import BaseCommand
from core.models import categories, Category
from ._download_funcs import (geography,
                              download_freyr_model,
                              download_kaldi,
                              recreate_dirs,
                              ML_NAMES)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Команда скачивания новых версий ML-моделей'

    def handle(self, *args, **options):
        if options['loyalty']:
            download_freyr_model(name='article_sentiment')
            download_freyr_model(name='article_theme')
        if options['categories']:
            download_freyr_model(name='gov_categories')
        if options['appeal']:
            download_freyr_model(name='article_appeal')
        if options['comments']:
            download_freyr_model(name='comment_sentiment')
        if options['stopwords']:
            download_freyr_model(name='addenda')
        if options['kaldi']:
            download_kaldi()
        if options['geography']:
            geography()
        if options['full']:
            recreate_dirs()
            if Category.objects.all().count() == 0:
                for cat in categories:
                    Category.objects.create(name=cat)
            for name in ML_NAMES:
                download_freyr_model(name)
            geography()
            download_kaldi()


    def add_arguments(self, parser):
        commands = (
            ('--full', 'Полное обновление всех моделей системы',),
            ('--loyalty', 'Модели для индекса лояльности',),
            ('--categories', 'Модель для классификации категорий постов',),
            ('--appeal', 'Модель для выявления обращений граждан',),
            ('--comments', 'Модель для определения тональности комментариев',),
            ('--stopwords', 'Стоп-слова',),
            ('--kaldi', 'Модель для распознавания речи',),
            ('--geography', 'Наборы данных для работы с географией',),
        )

        for command, help in commands:
            parser.add_argument(
                command,
                action='store_true',
                default=False,
                help=help
            )
