from django.db import models
from .article import Article

categories = ('Без темы',
              'Доходы населения, бедность',
              'Спорт',
              'Здравоохранение',
              'Социальная защита',
              'Образование',
              'Строительство, ЖКХ',
              'Безопасность',
              'Культура',
              'Дорожное хозяйство и транспорт',
              'Возможности для бизнеса',
              'Возможности для работы',
              'Отношения с государством',
              'Социальные связи',
              'Торговля',
              'Экология',
              'Бюджетный и налоговый потенциал',
              'Государственные услуги')


class Category(models.Model):
    """Категории постов

    Fields:
        name: Название категории
    """
    name = models.TextField(verbose_name='Название категории')

    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class ArticleCategory(models.Model):
    """Категории статей

    Fields:
        post_id: Идентификатор статьи
        category_id: Идентификатор категории.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        related_name='categories',
        default=None,
        null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='posts_by_category',
        default=None,
        null=True)
    
    def __str__(self):
        return str(self.id)
    
    class Meta:
        verbose_name = 'Категории статьи'
        verbose_name_plural = 'Категории статей'
