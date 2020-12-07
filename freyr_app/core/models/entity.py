from django.db import models
from .article import Article

class Entity(models.Model):
    """Сущности, извлечённые из текста
    """
    NER_TYPES = (
        ('PER', 'Personality'),
        ('LOC', 'Locality'),
        ('ORG', 'Organization'),
    )
    name = models.TextField(verbose_name='Имя')
    type = models.CharField(verbose_name='Тип', max_length=30, choices=NER_TYPES)
    
    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = 'Сущность'
        verbose_name_plural = 'Сущности'

        
class EntityLink(models.Model):
    """Связи сущностей и статей
    """
    entity_link = models.ForeignKey(Entity,
        on_delete=models.SET_NULL,
        related_name='entity_articles',
        verbose_name='Статьи сущности',
        null=True,
        )
    article_link = models.ForeignKey(Article,
        on_delete=models.SET_NULL,
        related_name='article_entities',
        verbose_name='Сущности статьи',
        null=True,
        )
    
    def __str__(self):
        return str(self.entity_link)
    
    class Meta:
        verbose_name = 'Ссылка сущности'
        verbose_name_plural = 'Ссылки сущностей'
    