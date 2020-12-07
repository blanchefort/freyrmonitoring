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
        theme - 1 - относится к нашей теме, 0 - нет
        sentiment - тональность:
            1 - положительный
            0 - нейтральный
            2 - отрицательный
        likes - количество лайков
    """
    SENTIMENT_TYPES = (
        (0, 'Нейтральный'),
        (1, 'Положительный'),
        (2, 'Отрицательный')
    )

    url = models.URLField(verbose_name='URL статьи', max_length=512, unique=True)
    site = models.ForeignKey(Site,
        on_delete=models.SET_NULL,
        related_name='site_articles',
        verbose_name='Статья сайта',
        null=True,
        )
    title = models.TextField(verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    publish_date = models.DateTimeField(
        auto_now_add=False,
        verbose_name='Дата'
        )
    theme = models.BooleanField(verbose_name='В индексе отслеживания', default=False)
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
    
    def __str__(self):
        return str(self.url)
    
    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-publish_date']
        