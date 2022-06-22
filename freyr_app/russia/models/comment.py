"""Комментарии к материалам"""

from django.db import models
from .article import Article


class Comment(models.Model):
    """Комментарии к сохранённым статьям и постам

    Args:
        article - идентификатор статьи или поста, к которому относится комментарий
        system_id - идентификатор комментария во внешней системе
        parent_system_id - идентификатор верхнеуровнего комментария в системе
        text - текст комментария
        publish_date - дата публикации
        sentiment - общая тональность комментария
        likes - лайки комментария
        dislikes - дизлайки комментария
        username - имя пользователя, оставившего комментарий
        userid - идентификатор комментатора
    """
    SENTIMENT_TYPES = (
        (0, 'Нейтральный'),
        (1, 'Положительный'),
        (2, 'Отрицательный'),
        (9, 'Не размечен'),
    )
    article = models.ForeignKey(Article,
        on_delete=models.SET_NULL,
        related_name='comment_articles',
        verbose_name='Статья комментария',
        null=True,
        )
    system_id = models.PositiveIntegerField(
        verbose_name='ID коммента во внешней системе',
        blank=True,
        null=True,
    )
    parent_system_id = models.PositiveIntegerField(
        verbose_name='ID верхнего коммента во внешней системе',
        blank=True,
        null=True,
    )
    text = models.TextField(verbose_name='Текст')
    publish_date = models.DateTimeField(
        auto_now_add=False,
        verbose_name='Дата'
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
        null=True,
    )
    dislikes = models.PositiveIntegerField(
        verbose_name='Дизлайки',
        default=0,
        null=True
    )
    username = models.CharField(
        max_length=120,
        verbose_name='Имя комментатора',
        blank=True,
        null=True,
    )
    userid = models.CharField(
        max_length=120,
        verbose_name='Идентификатор комментатора во внешней системе',
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.text)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-publish_date']
