import os, shutil
import logging
from django.conf import settings
from core.processing.nlp import get_title
from core.models import Article, Comment, ArticleDistrict, Theme, ThemeArticles, ThemeMarkup
from core.processing.markup_content import localize
from core.processing.markup_content import appeals as appl
from core.processing.predictor import DefineText
from core.processing.clustering import TextStreamClustering
from core.processing.search import FaissSearch

logger = logging.getLogger(__name__)


def titles():
    """Создание заголовков для всех постов из соцсетей
    """
    articles = Article.objects\
        .exclude(site__type='site')\
        .exclude(site__type='youtube')
    if articles.count() > 0:
        logger.info(f'Выбрано {articles.count()} постов для генерации заголовков')
        logger.info('Начало генерации заголовков')
        for article in articles:
            article.title = get_title(article.text)
            article.save()
    else:
        logger.info('Нет подходящих постов для генерации заговоков')
    logger.info('Конец генерации заголовков')


def appeals():
    """Выявление в статьях обращений к органам власти"""
    articles = Article.objects.all()
    if articles.count() > 0:
        logger.info("Recalculate Appeals' Flags for Articles")
        appl(articles)
        logger.info("Recalculating Finished!")
    else:
        logger.info('No Articles')


def geo():
    """Пересчёт привязки статей к муниципалитетам"""
    articles = Article.objects.all()
    if articles.count() == 0:
        logger.info('Пока нет статей для пересчёта. Выходим...')
        return False
    logger.info('Удаление предыдущих гео-привязок')
    ArticleDistrict.objects.all().delete()
    logger.info('Начало определения локализации статей')
    logger.info(f'Количество материалов: {articles.count()}')
    localize(articles)
    logger.info('Определения локализации статей успешно закончено')
    return True


def loyalty():
    """Пересчитать индекс лояльности"""
    articles = Article.objects.all()
    if articles.count() == 0:
        logger.info('Пока нет статей для пересчёта. Выходим...')
        return False
    logger.info('Начало пересчёта индекса лояльности')
    logger.info(f'Количество материалов: {articles.count()}')
    texts = [item.text for item in articles]
    dt = DefineText(texts)
    themes, _ = dt.article_theme()
    sentiments, _ = dt.article_sentiment()

    for article, theme, sentiment in zip(articles, themes, sentiments):
        article.theme = bool(theme)
        article.sentiment = sentiment
        article.save()


# def clustering():
#     """Новая кластеризация. Старые кластеры будут удалены, кластеризуются лишь последние новые материалы."""
#     logger.warning('Новая кластеризация.')

#     Theme.objects.all().delete()
#     ThemeArticles.objects.all().delete()
#     ThemeMarkup.objects.all().delete()
#     logger.info('Все кластеры удалены')
    
#     articles = Article.objects.filter(theme=True)
#     if len(articles) < 5:
#         logger.info(f'Недостаточно статей для кластеризации')
#         return False
    
#     logger.info('Приступаем к новой кластеризации')
#     clusterer = TextStreamClustering()
#     titles = [a.title for a in articles]
#     texts = [a.text for a in articles]
#     clusters = clusterer.clustering(texts, titles)

#     for cluster in clusters:
#         theme = Theme.objects.create(
#             name=titles[cluster[0]],
#             keywords=texts[cluster[0]]
#         )
#         for idx in cluster:
#             ThemeArticles(
#                 theme_link=theme,
#                 article_link=articles[idx]
#             ).save()

def clustering():
    logger.warning('Новая кластеризация. Старые кластеры будут удалены.')
    Theme.objects.all().delete()
    ThemeArticles.objects.all().delete()
    ThemeMarkup.objects.all().delete()
    logger.info('Все кластеры удалены')

    articles_full = Article.objects.filter(theme=True).order_by('-publish_date')
    clusterer = TextStreamClustering()

    step = 500

    logger.info(f'Количество материалов: {len(articles_full)}. Количество шагов: {int(len(articles_full)/step)}')

    s = 0
    for batch in range(0, len(articles_full), step):
        articles = articles_full[batch:batch+step]
        logger.info(f'Шаг {s}')
        titles = [a.title for a in articles]
        texts = [a.text for a in articles]
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


def indexing() -> None:
    """Индексация для поиска: индексируем статьи"""
    articles = Article.objects.all()
    if articles.count() == 0:
        logger.warning('Нечего индексировать. Выходим.')
    logger.info(f'Начинаем создание нового индекса. Всего статей: {len(articles)}')
    indexer = FaissSearch()
    items_index = [a.title + ' ' + a.text for a in articles]
    cnt = indexer.create_index(items_index)
    indexer.save()
    for idx, a in enumerate(articles):
        a.search_idx = idx
        a.save()
    logger.info(f'Создан индекс на {cnt} статей.')
