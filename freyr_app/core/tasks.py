from __future__ import absolute_import, unicode_literals
from celery import shared_task
from processing.crawlers import *
from processing.predictor import DefineText
from processing.nlp import ner
from core.models.site import Site
from core.models.article import Article
from core.models.site import Site
from core.models.entity import Entity, EntityLink
from django.conf import settings
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from core.models.theme import Theme, ThemeArticles
import numpy as np
import torch
import os
from processing.clustering import *

@shared_task(name='sites_article_collector')
def article_collector():
    """Метод обходит все площадки и собирает с них статьи
    TODO: Добавить мультипроцессинг
    """
    sites = Site.objects.all()
    for site in sites:
        # Предустановленные методы для заказчика
#         сломался
#         if 'https://newsroom24.ru/archive/' in site.url:
#             result = get_newsroom24()
#             if result is not None and len(result) > 0:
#                 print('Downloaded:', site.url, len(result))
#                 save_articles(result, site.url)
        if 'https://www.vgoroden.ru/' in site.url:
            result = get_vgoroden()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://newsnn.ru/' in site.url:
            result = get_newsnn()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://progorodnn.ru/news' in site.url:
            result = get_progorodnn()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://nn-now.ru/' in site.url:
            result = get_nnnow()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://pravda-nn.ru/' in site.url:
            result = get_pravdann()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://koza.press/' in site.url:
            result = get_koza()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'https://opennov.ru/news' in site.url:
            result = get_opennov()
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        # Общие методы
        if 'site' == site.type:
            result = get_standalone_site(site.url)
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'kp' == site.type:
            result = get_kp(site.url)
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'mk' == site.type:
            result = get_mk(site.url)
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'kommersant' == site.type:
            result = get_kommersant(site.url)
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        if 'vesti' == site.type:
            result = get_vesti(site.url)
            if result is not None and len(result) > 0:
                print('Downloaded:', site.url, len(result))
                save_articles(result, site.url)
        
    return True

def comment_collector():
    """Метод обходит все недавние статьи и собирает с них лайки и комментарии
    """
    pass

def social_collector():
    """Метод собирает посты из соцсетей
    """
    pass

def save_articles(articles, site_url):
    """Сохраняем статьи ресурса
    """
    texts = [item['text'] for item in articles]
    themes, sentiments = [], []
    dt = DefineText(texts=texts, model_path=settings.ML_MODELS)
    themes, _ = dt.article_theme()
    sentiments, _ = dt.article_sentiment()
    
    for item, t, s in zip(articles, themes, sentiments):
        if Article.objects.filter(url=item['url']).count() == 0:
            article_id = Article.objects.create(
                url=item['url'],
                site=Site.objects.get(url=site_url),
                title=item['title'],
                text=item['text'],
                publish_date=item['date'] or datetime.now(),
                theme=t,
                sentiment=s
            )
            # Сущности
            # Здравствуйте, на ул. Мечникова д. 47 подъезд 2 нет воды, с 15.08.2020
            # Наташа размечает улицу как фамилию
            if t == 1:
                entities = ner(item['text'])
                for entity in entities:
                    obj, created = Entity.objects.get_or_create(name=entity[0], type=entity[1])
                    EntityLink.objects.create(
                        entity_link=obj,
                        article_link=article_id
                    )
    return True

# @shared_task(name='redefine_current_themes')
# def define_theme():
#     """Распределяем статьи по темам
#     TODO: сделать что-то с хронологией
#     """
#     top_k = 5
#     themes = Theme.objects.all()
#     articles = Article.objects.filter(theme=True).all()
#     #articles_texts = [str(article.title) for article in articles]
#     articles_texts = [str(article.text) for article in articles]
    
#     model = SentenceTransformer('distiluse-base-multilingual-cased')
#     corpus_embeddings = model.encode(articles_texts)
    
#     ThemeArticles.objects.all().delete()
#     for theme in themes:
#         theme_text = theme.name + ', ' + theme.keywords
#         theme_embedding = model.encode(theme_text, convert_to_tensor=True)
#         cos_scores = util.pytorch_cos_sim(theme_embedding, corpus_embeddings)[0]
#         cos_scores = cos_scores.cpu()
#         top_results = np.argpartition(-cos_scores, range(top_k))
#         for idx in top_results:
#             if cos_scores[idx].item() > .35:
#                 ThemeArticles(
#                     theme_link=theme,
#                     article_link=articles[idx.item()]
#                 ).save()

#     return True

@shared_task(name='define_themes')
def define_theme():
    '''Семантическая кластеризация материалов
    '''
    themes = Theme.objects.all()
    if len(themes) == 0:
        # Тем нет, проводим начальную кластеризацию
        articles = Article.objects.filter(theme=True).all()
        print('articles len', len(articles))
        if len(articles) == 0:
            return True
        lag_idx = []
        lag_titles = []
        lag_texts = []
        for article in articles:
            lag_idx.append(article.id)
            lag_titles.append(article.title)
            lag_texts.append(article.text)
        
        print('generate_corpus_embs')
        corpus_embeddings = generate_corpus_embs(titles=lag_titles, texts=lag_texts)
        print('generate_new_clusters')
        (cluster_embeddings, 
         cluster_titles, 
         cluster_keywords, 
         cluster_articles) = generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)
        print('save clusters and links')
        for cl_idx in range(0, len(cluster_embeddings)):
            theme_id = Theme.objects.create(
                name=cluster_titles[cl_idx],
                keywords=cluster_keywords[cl_idx]
            )
            torch.save(cluster_embeddings, os.path.join(settings.CLUSTERS_PATH, f'{theme_id}.pt'))
            theme = Theme.objects.get(theme_id)
            for art_id in get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
                ThemeArticles(
                    theme_link=theme,
                    article_link=Article.objects.get(art_id)
                ).save()
    else:
        # кластеры уже есть, прогоняем последние статьи
        # берём новые статьи за последние N часов
        # 'schedule': crontab(minute=25, hour='*/12'),
        pass
        
    return True
