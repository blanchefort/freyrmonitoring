from django.db import models
from .district import District
from .category import Category


class Happiness(models.Model):
    """Сводные таблицы индекса счастья

    Args:
        SOURCE_TYPES - тип источника данных
            SYSTEM - сформированные системой FreyrMonitoring на своих данных
            EXTERNAL - загруженные внешние показатели
    """
    SOURCE_TYPES = (
        (0, 'SYSTEM'),
        (1, 'EXTERNAL')
    )
    source_type = models.PositiveSmallIntegerField(
        verbose_name='Тип источника данных',
        choices=SOURCE_TYPES
    )
    name = models.CharField(
        verbose_name='Заголовок набора данных',
        max_length=256
    )
    start_period = models.DateField(
        verbose_name='Начало периода',
        auto_now_add=True,
    )
    end_period = models.DateField(
        verbose_name='Конец периода',
        auto_now_add=True,
    )
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='district_happy_index',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_happy_index',
    )
    value = models.FloatField(
        verbose_name='Показатель'
    )

    def __str__(self):
        return f'{self.name}: {self.value}'
    
    class Meta:
        verbose_name = 'Показатели индекса счастья'
        verbose_name_plural = 'Показатели индекса счастья'
