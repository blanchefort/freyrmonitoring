"""Посты и новостные статьи"""
from django.db import models
from .site import Site


class Article(models.Model):
    """Статьи, скачанные краулером
    
    Args:
        url - полная ссылка на материал, либо иной идентификатор
        site - идентификатор площадки
        title - заголовок материала
        text - полный текст материала
        publish_date - дата публикации
        author - автор материала
        theme - True, если в индексе, False - если рекламный пост
        sentiment - общая тональность
        likes - количество лайков
        dislikes - дизлайки
        views - количество просмотров
        search_idx - идентификатор в поисковом индексе
    """

    SENTIMENT_TYPES = (
        (0, 'Нейтральный'),
        (1, 'Положительный'),
        (2, 'Отрицательный'),
        (9, 'Не размечен'),
    )

    url = models.URLField(verbose_name='URL статьи', max_length=512)
    site = models.ForeignKey(Site,
        on_delete=models.SET_NULL,
        related_name='site_articles',
        verbose_name='Статья сайта',
        null=True,
    )
    title = models.TextField(
        verbose_name='Заголовок',
        blank=True,
        null=True
    )
    text = models.TextField(verbose_name='Текст')
    publish_date = models.DateTimeField(
        auto_now_add=False,
        verbose_name='Дата'
    )
    author = models.TextField(
        verbose_name='Автор',
        blank=True,
        null=True
    )
    theme = models.BooleanField(
        verbose_name='В индексе отслеживания',
        default=False
    )
    sentiment = models.PositiveSmallIntegerField(
        verbose_name='Тональность',
        blank=True,
        null=True,
        choices=SENTIMENT_TYPES
    )
    likes = models.PositiveIntegerField(
        verbose_name='Лайки',
        default=0,
        null=True
    )
    dislikes = models.PositiveIntegerField(
        verbose_name='Дизлайки',
        default=0,
        null=True
    )
    views = models.PositiveIntegerField(
        verbose_name='Просмотры',
        default=0,
        null=True
    )
    search_idx = models.PositiveIntegerField(
        verbose_name='Поисковый индекс',
        default=None,
        null=True
    )

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-publish_date']
