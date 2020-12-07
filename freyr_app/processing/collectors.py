"""Тестируем методы, которые будут включаться по расписанию
"""
from processing.crawlers import *
from processing.predictor import DefineText
from processing.nlp import ner
from core.models.site import Site
from core.models.article import Article
from core.models.site import Site
from core.models.entity import Entity, EntityLink
from django.conf import settings

def article_collector():
    """Метод обходит все площадки и собирает с них статьи
    TODO: Добавить мультипроцессинг
    """
    sites = Site.objects.all()
    for site in sites:
        # Предустановленные методы для заказчика
        if 'https://newsroom24.ru/archive/' in site.url:
            result = get_newsroom24()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://www.vgoroden.ru/' in site.url:
            result = get_vgoroden()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://newsnn.ru/' in site.url:
            result = get_newsnn()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://progorodnn.ru/news' in site.url:
            result = get_progorodnn()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://nn-now.ru/' in site.url:
            result = get_nnnow()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://pravda-nn.ru/' in site.url:
            result = get_pravdann()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://koza.press/' in site.url:
            result = get_koza()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'https://opennov.ru/news' in site.url:
            result = get_opennov()
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        # Общие методы
        if 'site' == site.type:
            result = get_standalone_site(site.url)
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'kp' == site.type:
            result = get_kp(site.url)
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'mk' == site.type:
            result = get_mk(site.url)
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'kommersant' == site.type:
            result = get_kommersant(site.url)
            if result is not None and len(result) > 0:
                save_articles(result, site.url)
        if 'vesti' == site.type:
            result = get_vesti(site.url)
            if result is not None and len(result) > 0:
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
                publish_date=item['date'],
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
        
    
    