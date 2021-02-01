import logging
from core.processing.nlp import get_title
from core.models import Article, Comment, ArticleDistrict
from core.processing.markup_content import localize
from core.processing.markup_content import appeals as appl
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