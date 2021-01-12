"""Размечаем неразмеченный контент
"""
import logging
from core.models import Article, Category, ArticleCategory, Comment
from core.processing.nlp import get_title, deEmojify
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
        texts = [deEmojify(item.text) for item in articles]
        dt = DefineText(texts)
        themes, _ = dt.article_theme()
        sentiments, _ = dt.article_sentiment()

        for article, theme, sentiment in zip(articles, themes, sentiments):
            article.theme = bool(theme)
            article.sentiment = sentiment
            article.save()

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

def ner():
    """Извлечение именованных сущностей из размеченных статей
    """
    pass