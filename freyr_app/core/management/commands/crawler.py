"""Команда для сбора новых данных из интернета

Использование:

$python manage.py collector
"""
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from processing.predictor import DefineText
from processing.nlp import ner
from core.models.site import Site
from core.models.article import Article
from core.models.entity import Entity, EntityLink
from core.crawlers import (
    get_newsroom24,
    get_vgoroden,
    get_newsnn,
    get_progorodnn,
    get_koza,
    get_pravdann
)
from core.crawlers import YTParser
import configparser
from processing.clustering import TextStreamClustering
from core.models.theme import Theme, ThemeArticles
import torch
import datetime
import time
import schedule

def scrape_custom_sites():
    """Обходим и сохраняем сайты с индивидуальными парсерами
    """
    print('Start Custom Sites Scraping')

    #newsroom24
    site, _ = Site.objects.get_or_create(url='https://newsroom24.ru/archive/', title='newsroom24.ru', type='site')
    print(site)
    result = get_newsroom24()
    print('Found articles', len(result))
    if result is not None and len(result) > 0:
        save_articles(result, site.url)
    print()

    #vgoroden
#     site, _ = Site.objects.get_or_create(url='https://www.vgoroden.ru/', title='vgoroden.ru', type='site')
#     print(site)
#     result = get_vgoroden()
#     print('Found articles', len(result))
#     if result is not None and len(result) > 0:
#         save_articles(result, site.url)
#     print()

    #get_newsnn
    site, _ = Site.objects.get_or_create(url='https://newsnn.ru/', title='newsnn.ru', type='site')
    print(site)
    result = get_newsnn()
    print('Found articles', len(result))
    if result is not None and len(result) > 0:
        save_articles(result, site.url)
    print()

    #get_progorodnn
    site, _ = Site.objects.get_or_create(url='https://progorodnn.ru/news', title='progorodnn.ru', type='site')
    print(site)
    result = get_progorodnn()
    print('Found articles', len(result))
    if result is not None and len(result) > 0:
        save_articles(result, site.url)
    print()

    #get_koza
    site, _ = Site.objects.get_or_create(url='https://koza.press/', title='koza.press', type='site')
    print(site)
    result = get_koza()
    print('Found articles', len(result))
    if result is not None and len(result) > 0:
        save_articles(result, site.url)
    print()

    #get_pravdann
    site, _ = Site.objects.get_or_create(url='https://pravda-nn.ru/', title='pravda-nn.ru', type='site')
    print(site)
    result = get_pravdann()
    print('Found articles', len(result))
    if result is not None and len(result) > 0:
        save_articles(result, site.url)
    print()

    print('Custom Sites Scraping complete!')


def save_articles(articles, site_url):
    """Сохраняем статьи ресурса
    """
    texts = [item['text'] for item in articles]
    themes, sentiments = [], []
    dt = DefineText(texts=texts, model_path=settings.ML_MODELS)
    themes, _ = dt.article_theme()
    sentiments, _ = dt.article_sentiment()

    current_tz = timezone.get_current_timezone()

    for item, t, s in zip(articles, themes, sentiments):
        if Article.objects.filter(url=item['url']).count() == 0:
            article_id = Article.objects.create(
                url=item['url'],
                site=Site.objects.get(url=site_url),
                title=item['title'],
                text=item['text'],
                publish_date=current_tz.localize(item['date']),
                theme=t,
                sentiment=s
            )
            # Сущности
            if t == 1:
                entities = ner(item['text'])
                for entity in entities:
                    obj, created = Entity.objects.get_or_create(name=entity[0], type=entity[1])
                    EntityLink.objects.create(
                        entity_link=obj,
                        article_link=article_id
                    )
    return True

def clustering(delta_hours=5):
    """Кластеризуем материалы
    
    delta_hours - за сколько предыдущих часов брать статьи из БД для кластеризации.
    """
    print('Start Clustering')
    themes = Theme.objects.all()
    tsc = TextStreamClustering()
    if len(themes) == 0:
        print('New Clustering')
        articles = Article.objects.filter(theme=True).all()

        lag_idx = [article.id for article in articles]
        lag_titles = [article.title for article in articles]
        lag_texts = [article.text for article in articles]
        
        print('generate_corpus_embs')
        corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)

        print('generate_new_clusters')
        (cluster_embeddings, 
        cluster_titles, 
        cluster_keywords, 
        cluster_articles) = tsc.generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)

        print('save clusters and links')
        for cl_idx in range(0, len(cluster_embeddings)):
            theme = Theme.objects.create(
                name=cluster_titles[cl_idx],
                keywords=cluster_keywords[cl_idx]
            )
            torch.save(cluster_embeddings[cl_idx], os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
            for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
                ThemeArticles(
                    theme_link=theme,
                    article_link=Article.objects.get(pk=art_id)
                ).save()
    else:
        print('TimeSiquenceClustering')
        delta_hours = -delta_hours
        start_date = timezone.now()
        end_date = timezone.now() + datetime.timedelta(hours=delta_hours)
        articles = Article.objects.filter(theme=True).filter(
                    publish_date__gte=end_date,
                    publish_date__lte=start_date
                )
        print('Len of articles', len(articles))
        lag_idx = [article.id for article in articles]
        lag_titles = [article.title for article in articles]
        lag_texts = [article.text for article in articles]
        # Получаем эмбеддинги новой выборки
        print('Получаем эмбеддинги новой выборки')
        corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)
        # Прогоняем статьи по имеющимся кластерам
        print('Прогоняем статьи по имеющимся кластерам')
        selected_articles = []
        #TODO: Темы надо тоже по времени ограничивать
        for theme in themes:
            cluster_new_articles = []
            cluster_embedding = torch.load(os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
            selected, _, _ = tsc.select_cluster_articles(cluster_embedding, corpus_embeddings)
            if len(selected) > 0:
                cluster_new_articles = selected
                selected_articles += selected
            # Идентификаторы статей кластера для сохранения в БД
            for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_new_articles):
                ThemeArticles.objects.get_or_create(
                    theme_link=theme,
                    article_link=Article.objects.get(pk=art_id)
                )
        # Смотрим, остались ли ещё неразмеченные статьи
        print('Смотрим, остались ли ещё неразмеченные статьи')
        if len(set(selected_articles)) < len(lag_idx):
            lag_idx, lag_titles, lag_texts = tsc.get_nonclustered_data(
                lag_idx=lag_idx,
                lag_titles=lag_titles,
                lag_texts=lag_texts,
                clustered_ids=set(selected_articles))
            corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)

            # Новые кластеры
            print('Новые кластеры')
            (cluster_embeddings, 
            cluster_titles, 
            cluster_keywords, 
            cluster_articles) = tsc.generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)

            # Сохраняем новые кластеры
            print('Сохраняем новые кластеры')
            for cl_idx in range(0, len(cluster_embeddings)):
                theme = Theme.objects.create(
                    name=cluster_titles[cl_idx],
                    keywords=cluster_keywords[cl_idx]
                )
                torch.save(cluster_embeddings[cl_idx], os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
                for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
                    ThemeArticles.objects.get_or_create(
                        theme_link=theme,
                        article_link=Article.objects.get(pk=art_id)
                    )
            print('End Clustering')


def test_yt():
    """Тестовая версия краулера Ютуба
    """
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
    print('YOUTUBE LINK COUNT:', link_counter)

def job():
    scrape_custom_sites()
    test_yt()
    clustering(delta_hours=3)
    print('Ok!')

class Command(BaseCommand):
    help = 'Запуск сборщика новых данных из соцсетей'

    def handle(self, *args, **kwargs):
        scrape_custom_sites()
        test_yt()
        clustering(delta_hours=15)
        schedule.every(2).hours.do(job)

        while True:
            schedule.run_pending()
            time.sleep(1)