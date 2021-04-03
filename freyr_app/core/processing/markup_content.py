"""Размечаем неразмеченный контент
"""
import logging
import time
import datetime
from nltk.metrics import distance
from django.utils import timezone
from ..models import (
    Article,
    Category,
    ArticleCategory,
    Comment,
    District,
    ArticleDistrict,
    Entity,
    EntityLink,
    Theme,
    ThemeArticles
)
from .nlp import get_title, deEmojify, ner, get_district
from .predictor import DefineText
from core.processing.search import FaissSearch
from core.processing.clustering import TextStreamClustering

logger = logging.getLogger(__name__)


def create_titles():
    """Создание заголовков статей
    """
    logger.info('CREATE TITLES')
    for article in Article.objects.filter(title='(без заголовка)'):
        article.title = get_title(article.text)
        article.save()


def markup_theme():
    """Разметка темы и тональности (отношение к власти) статей
    """
    articles = Article.objects.exclude(sentiment=0).exclude(sentiment=1).exclude(sentiment=2)
    if len(articles) == 0:
        return False
    logger.info('Определяем отношение к власти в материалах')
    texts = [item.text for item in articles]
    dt = DefineText(texts)
    themes, _ = dt.article_theme()
    sentiments, _ = dt.article_sentiment()

    for article, theme, sentiment in zip(articles, themes, sentiments):
        article.theme = bool(theme)
        article.sentiment = sentiment
        article.save()
    logger.info('Определение отношения к власти закончено')
    # Сущности
    ner_articles(articles)
    # Жалобы граждан
    appeals(articles)
    # Поисковые статьи
    update_search_index(articles)


def article_happiness():
    """Разметка тональность статей для индекса благополучия
    """
    articles = Article.objects\
        .exclude(happiness_sentiment=0)\
        .exclude(happiness_sentiment=1)\
        .exclude(happiness_sentiment=2)
    if len(articles) > 0:
        logger.info('DEFINE HAPPINESS THEME AND SENTIMENT')
        texts = [deEmojify(item.text) for item in articles]
        dt = DefineText(texts)
        themes, _ = dt.happiness_category()
        sentiments, _ = dt.happiness_sentiment()
        for article, theme, sentiment in zip(articles, themes, sentiments):
            for t in theme:
                ArticleCategory(
                    article=article,
                    category=Category.objects.get(name=t)
                ).save()
            article.happiness_sentiment = sentiment
            article.save()
        
        # привязка к муниципалитетам
        localize(articles)


def comment_sentiment():
    """Тональность комментариев
    """
    comments = Comment.objects.exclude(sentiment=0).exclude(sentiment=1).exclude(sentiment=2)
    if len(comments) > 0:
        logger.info('DEFINE COMMENTS SENTIMENT')
        # TODO: Проверить, где выше качество - с эмоджи или без
        # texts = [item.text for item in comments]
        texts = [deEmojify(item.text) for item in comments]
        dt = DefineText(texts)
        sentiments, _ = dt.comment_sentiment()
        for comment, sentiment in zip(comments, sentiments):
            comment.sentiment = sentiment
            comment.save()


def ner_articles(articles: Article):
    """Извлечение именованных сущностей из размеченных статей
    """
    for article in articles:
        entities = ner(article.text)
        for ent in entities:
            if ent[1] in ('PER', 'LOC', 'ORG', ) and ent[0] is not None:
                entity, _ = Entity.objects.get_or_create(
                    name=ent[0],
                    type=ent[1]
                )
                EntityLink(
                    entity_link=entity,
                    article_link=article
                ).save()


def localize(articles: Article):
    """Выявление муниципалитетов, о которых идёт речь в статьях
    """
    districts = District.objects.all()
    for article in articles:
        entities = ner(article.text)
        for ent in entities:
            if ent[1] == 'LOC' and ent[0] is not None:
                location = get_district(ent[0])
                if location is not False:
                    for district in districts:
                        location = location.replace('Город ', '')
                        # if location == 'Россия':
                        #     location = 'region'
                        location = location.lower()
                        district_name = district.name.lower()
                        if 'городской округ' in district_name:
                            district_name = district_name.replace('городской округ', '')
                        dist = distance.edit_distance(location, district_name)
                        if dist < 2:
                            ArticleDistrict(
                                article=article,
                                district=district
                            ).save()
                            break


def appeals(articles: Article):
    """Выявление жалоб граждан, на которые нужен ответ органов региональной власти"""
    if articles.count() > 0:
        logger.info("Выявление жалоб граждан")
        texts = [a.text for a in articles]
        dt = DefineText(texts)
        is_appeal, _ = dt.is_appeal()
        for article, appeal in zip(articles, is_appeal):
            article.appeal = appeal
            article.save()
        logger.info("Выявление жалоб граждан завершено")


def update_search_index(articles: Article):
    """Обновляем поисковый индекс
    """
    logger.info("Обновляем поисковый индекс")
    items_index = [a.title + ' ' + a.text for a in articles]
    if len(items_index) == 0:
        logger.info('Нет материалов для индекции. Выходим')
        return False
    indexer = FaissSearch()
    indexer.load()
    start_idx, cnt = indexer.add(items_index)
    indexer.save()
    for idx, a in zip(range(start_idx, cnt), articles):
        a.search_idx = idx
        a.save()
    logger.info(f'Общий размер индекса: {cnt}')


def clustering(delta_hours: int = 5):
    """Кластеризация

    Args:
        delta_hours (int, optional): за сколько предыдущих часов брать статьи из БД для кластеризации.
    """
    start_date = timezone.now()
    end_date = timezone.now() + datetime.timedelta(hours=delta_hours)
    articles = Article.objects.filter(theme=True).filter(
        publish_date__gte=end_date,
        publish_date__lte=start_date
    )
    if len(articles) < 5:
        return False
    
    logger.info(f'Начало кластеризации')
    end_date = timezone.now() - datetime.timedelta(hours=5*24)
    themes = Theme.objects.filter(
        theme_articles__article_link__publish_date__range=[end_date, start_date])
    
    titles = [a.title for a in articles]
    texts = [a.text for a in articles]

    clusterer = TextStreamClustering()
    if len(themes) > 0:
        clust_texts = [t.name for t in themes]
        clust_titles = [t.keywords for t in themes]
        clustered_ids, clusters = clusterer.continuous_clustering(
            texts, 
            titles, 
            clust_texts, 
            clust_titles)
        for clister_idx in clustered_ids.keys():
            theme = Theme.objects.get(pk=clister_idx)
            for article_idx in clustered_ids[clister_idx]:
                ThemeArticles(
                    theme_link=theme,
                    article_link=articles[article_idx]
                ).save()
    else:
        clusters = clusterer.clustering(texts, titles)
        
    for cluster in clusters:
        theme = Theme.objects.create(
            name=titles[cluster[0]],
            keywords=texts[cluster[0]]
        )
        for idx in cluster:
            ThemeArticles(
                theme_link=theme,
                article_link=articles[idx]
            ).save()


    logger.info(f'Окончание кластеризации')
    
    

    
