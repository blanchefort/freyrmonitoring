import logging
from core.processing.nlp import get_title
from core.models import Article, Comment, ArticleDistrict
from core.processing.predictor import DefineText
from core.processing.markup_content import localize
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
        texts = [a.text for a in articles]
        dt = DefineText(texts)
        is_appeal, _ = dt.is_appeal()
        for article, appeal in zip(articles, is_appeal):
            article.appeal = appeal
            article.save()
    logger.info("Recalculating Finished!")


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