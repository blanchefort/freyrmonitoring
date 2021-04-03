"""Команда для сбора новых данных по расписанию

Использование:

$python manage.py crawler
"""
import warnings
warnings.filterwarnings("ignore")
import os
import time
import schedule
import logging
import asyncio
from django.core.management.base import BaseCommand
from core.processing.scrape_socio import (
    collect_socio_posts,
    collect_comments,
    collect_telega_posts)
from core.processing.markup_content import (
    create_titles,
    markup_theme,
    article_happiness,
    comment_sentiment,
    update_search_index,
    clustering
)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
logger = logging.getLogger(__name__)


def tg_run():
    """Сбор данных их Телеграма
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(collect_telega_posts())


def crawler_step():
    """Полный цикл сбора информации
    """
    logger.info('Начало работы краулера')
    tg_run()
    collect_socio_posts()
    collect_comments()
    logger.info('Окончание работы краулера')


def processing_step():
    """Полный цикл обработки собранной информации
    """
    logger.info('Начало обработки контента')
    create_titles()
    markup_theme()
    article_happiness()
    comment_sentiment()
    clustering(delta_hours=25)
    logger.info('Окончание обработки контента')


class Command(BaseCommand):
    help = 'Запуск сборщика данных по расписанию'

    def handle(self, *args, **kwargs):
        crawler_step()
        processing_step()
        
        schedule.every().day.at('11:00').do(processing_step)
        schedule.every().day.at('03:00').do(processing_step)

        while True:
            schedule.run_pending()
            time.sleep(1)
