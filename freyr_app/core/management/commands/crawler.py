"""Команда для сбора новых данных из интернета

Использование:

$python manage.py collector
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.processing.predictor import DefineText
from core.models import Site, Article

from core.crawlers import YTParser
import configparser
import time
import schedule

from core.processing.clustering import clustering
from core.processing.custom_sites import scrape_custom_sites

import logging
logger = logging.getLogger(__name__)

def test_yt():
    """Тестовая версия краулера Ютуба
    """
    logger.info('START YOUTUBE')
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    yt = YTParser(
            api=config['YOUTUBE']['KEY'],
            audio_path=settings.AUDIO_PATH,
            kaldi_path=settings.KALDI
        )
    # Добавляем сайт
    channel, _ = Site.objects.get_or_create(
        url='https://www.youtube.com/user/SetiNNstation',
        title='Кстати Новости Нижнего Новгорода',
        type='youtube'
    )
    # Получаем ссылки на последние ролики
    latest_links = yt.get_latest_videos_by_channel_link(url=channel.url)
    link_counter = 0
    for link in latest_links:
        if Article.objects.filter(url=link['url']).count() == 0:
            text, description = yt.video2data(link['url'])
            if len(text) > 0 and len(description) > 0:
                dt = DefineText(texts=[text], model_path=settings.ML_MODELS)
                theme, _ = dt.article_theme()
                sentiment, _ = dt.article_sentiment()
                Article.objects.create(
                    url=description['webpage_url'],
                    site=channel,
                    title=description['title'],
                    text=text,
                    publish_date=timezone.now(),
                    theme=theme[0],
                    sentiment=sentiment[0],
                    likes=description['like_count'],
                )
                link_counter += 1
    logger.info(f'YOUTUBE LINK COUNT: {link_counter}')

def job():
    logger.info('START CLUSTERING')
    clustering(delta_hours=24*30)

class Command(BaseCommand):
    help = 'Запуск сборщика новых данных из соцсетей'

    def handle(self, *args, **kwargs):
        logger.info('START CRAWLER')
        schedule.every(2).hours.do(scrape_custom_sites)
        schedule.every(6).hours.do(test_yt)
        schedule.every(8).hours.do(job)

        while True:
            schedule.run_pending()
            time.sleep(1)