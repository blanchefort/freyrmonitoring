"""Команда для сбора новых данных из интернета

Использование:

$python manage.py collector
"""
from django.core.management.base import BaseCommand

from core.processing.clustering import clustering
from core.processing.custom_sites import scrape_custom_sites
from core.processing.scrape_socio import collect_socio_posts, collect_commets

import logging
logger = logging.getLogger(__name__)


def job():
    logger.info('START CLUSTERING')
    try:
        clustering(delta_hours=24*5)
    except:
        logger.error('CLUSTERING FAILED')


class Command(BaseCommand):
    help = 'Запуск сборщика новых данных'

    def handle(self, *args, **kwargs):
        collect_socio_posts()
        collect_commets()
        scrape_custom_sites()
        clustering(delta_hours=24*5)
        
        logger.info('START CRAWLER')
        schedule.every(1).hours.do(collect_commets)
        schedule.every(2).hours.do(collect_socio_posts)
        schedule.every(4).hours.do(scrape_custom_sites)
        schedule.every(6).hours.do(job)

        while True:
            schedule.run_pending()
            time.sleep(1)
