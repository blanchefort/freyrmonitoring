from django.db import models
from .article import Article


class Theme(models.Model):
    """Выявленные темы для отслеживания
    """
    name = models.TextField(verbose_name='Заголовок')
    keywords = models.TextField(verbose_name='Ключевые слова')
    
    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'


class ThemeArticles(models.Model):
    """Статьи, относящиеся к кластеру
    """
    theme_link = models.ForeignKey(Theme,
        on_delete=models.SET_NULL,
        related_name='theme_articles',
        verbose_name='Статьи темы',
        null=True,
        )
    article_link = models.ForeignKey(Article,
        on_delete=models.SET_NULL,
        related_name='article_themes',
        verbose_name='Темы статьи',
        null=True,
        )
    
    def __str__(self):
        return str(self.theme_link)
    
    class Meta:
        verbose_name = 'Ссылка темы'
        verbose_name_plural = 'Ссылки тем'


class ThemeMarkup(models.Model):
    """Пользовательская разметка. 
    Пользовательские названия кластеров
    для обучения модели формирования заголовков.
    """
    theme = models.ForeignKey(Theme,
        on_delete=models.SET_NULL,
        related_name='theme_alt',
        verbose_name='Тема',
        null=True,
        )
    name = models.TextField(verbose_name='Альтернативный заголовок')

    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Альтернативный заголовок темы'
        verbose_name_plural = 'Альтернативные заголовоки тем'