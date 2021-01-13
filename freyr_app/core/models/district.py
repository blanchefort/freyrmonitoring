from django.db import models
from .article import Article

class District(models.Model):
    """Муниципалитеты

    Fields:
        name: Наименование муниципалитета.
    """
    name = models.CharField(
        verbose_name='Наименование муниципалитета',
        max_length=500,
        unique=True)

    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Муниципалитет'
        verbose_name_plural = 'Муниципалитеты'

class ArticleDistrict(models.Model):
    """Привязка статьи к муниципалитету
    """
    article = models.ForeignKey(Article,
        on_delete=models.SET_NULL,
        related_name='article_district',
        verbose_name='География статьи',
        null=True,
        )
    district = models.ForeignKey(District,
        on_delete=models.SET_NULL,
        related_name='district_article',
        verbose_name='Статья о муниципалитете',
        null=True,
        )
    
    def __str__(self):
        return f'{self.article}: {self.district}'
    
    class Meta:
        verbose_name = 'Привязка статьи к муниципалитету'
        verbose_name_plural = 'Привязка статьи к муниципалитету'