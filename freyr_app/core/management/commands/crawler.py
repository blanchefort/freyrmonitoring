"""Команда для сбора новых данных по расписанию

Использование:

$python manage.py crawler
"""
import warnings
import os
import time
import schedule
import logging
import asyncio
from django.core.management.base import BaseCommand
from core.processing.clustering import clustering
from core.processing.scrape_socio import (
    collect_socio_posts,
    collect_comments,
    collect_telega_posts)
from core.processing.markup_content import (
    create_titles,
    markup_theme,
    article_happiness,
    comment_sentiment,
)
warnings.filterwarnings("ignore")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
logger = logging.getLogger(__name__)


def clustering_step():
    """Кластеризация
    """
    logger.info('START CLUSTERING')
    try:
        clustering(delta_hours=24)
    except:
        logger.error('CLUSTERING FAILED')


def tg_run():
    """Сбор данных их Телеграма
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(collect_telega_posts())


def crawler_step():
    """Полный цикл сбора информации
    """
    logger.info('START CRAWLER')
    tg_run()
    collect_socio_posts()
    #scrape_custom_sites()
    collect_comments()
    logger.info('STOP CRAWLER')


def processing_step():
    """Полный цикл обработки собранной информации
    """
    logger.info('START CONTENT PROCESSING')
    create_titles()
    markup_theme()
    article_happiness()
    comment_sentiment()
    logger.info('END CONTENT PROCESSING')


class Command(BaseCommand):
    help = 'Запуск сборщика данных по расписанию'

    def handle(self, *args, **kwargs):
        crawler_step()
        processing_step()
        clustering_step()
        
        schedule.every().day.at('02:00').do(crawler_step)
        schedule.every().day.at('02:30').do(processing_step)
        schedule.every().day.at('05:00').do(clustering_step)

        while True:
            schedule.run_pending()
            time.sleep(1)
