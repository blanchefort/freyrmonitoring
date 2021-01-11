"""Команда для сбора новых данных по расписанию

Использование:

$python manage.py crawler
"""
import warnings
warnings.filterwarnings("ignore")
import os
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import time
import schedule
import logging
from asgiref.sync import async_to_sync, sync_to_async
import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand

from core.processing.clustering import clustering
from core.processing.custom_sites import scrape_custom_sites
from core.processing.scrape_socio import (
    collect_socio_posts,
    collect_comments,
    collect_telega_posts)
from core.crawlers import TelegaParser
from core.models import Site


logger = logging.getLogger(__name__)


def job():
    logger.info('START CLUSTERING')
    try:
        clustering(delta_hours=24*5)
    except:
        logger.error('CLUSTERING FAILED')

def tg_run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(collect_telega_posts())

class Command(BaseCommand):
    help = 'Запуск сборщика данных по расписанию'

    def handle(self, *args, **kwargs):
        logger.info('START CRAWLER')
        #tg_run()
        # await collect_telega_posts()
        # tg()
        # sync_to_async(collect_telega_posts)
        
        # schedule.every(1).hours.do(collect_telega_posts)
        # schedule.every(1).hours.do(collect_comments)
        # schedule.every(2).hours.do(collect_socio_posts)

        schedule.every().day.at('21:50').do(tg_run)
        # schedule.every().day.at('08:00').do(job)

        # schedule.every().day.at('10:00').do(collect_socio_posts)
        # schedule.every().day.at('10:30').do(job)


        while True:
            schedule.run_pending()
            time.sleep(1)
