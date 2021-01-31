"""Размечаем неразмеченный контент
"""
import logging
from nltk.metrics import distance
from core.models import (
    Article,
    Category,
    ArticleCategory,
    Comment,
    District,
    ArticleDistrict,
    Entity,
    EntityLink
)
from core.processing.nlp import get_title, deEmojify, ner, get_district
from core.processing.predictor import DefineText

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
    if len(articles) > 0:
        logger.info('DEFINE ARTICLE THEME AND SENTIMENT')
        # TODO: Теперь класс сам обрабатывает весь входящий текст, нужно убрать эту штуковину
        texts = [deEmojify(item.text) for item in articles]
        dt = DefineText(texts)
        themes, _ = dt.article_theme()
        sentiments, _ = dt.article_sentiment()

        for article, theme, sentiment in zip(articles, themes, sentiments):
            article.theme = bool(theme)
            article.sentiment = sentiment
            article.save()
    # Сущности
    ner_articles(articles)


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
                        location = location.replace('городской округ', '').strip().lower()
                        dist = distance.edit_distance(location, district.name.lower())
                        if dist < 2:
                            ArticleDistrict(
                                article=article,
                                district=district
                            ).save()
                            break

