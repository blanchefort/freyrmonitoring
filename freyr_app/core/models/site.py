from django.db import models

class Site(models.Model):
    """Площадки, которые обходит краулер
    
    Args:
        url - ссылка-вход для парсинга.
        title - заголовок площадки
        type - тип площадки.
    """
    SITE_TYPES = (
        ('site', 'Отдельный новостной сайт'),
        ('kp', 'Комсомольская правда'),
        ('mk', 'Московский комсомолец'),
        ('kommersant', 'Коммерсант'),
        ('vesti', 'Вести'),
        ('odnoklassniki_domain', 'Группа Одноклассники, доменное имя'),
        ('odnoklassniki_id', 'Группа Одноклассники, идентификатор'),
        ('insta', 'Инстаграм'),
        ('telega', 'Телеграм'),
        ('vk_domain', 'Группа Вконтакте доменное имя'),
        ('vk_owner', 'Группа Вконтакте идентификатор'),
        ('youtube', 'Ютуб-канал'),
        ('twi', 'Твиттер'),
        ('facebook', 'Твиттер'),
    )
    url = models.URLField(verbose_name='URL площадки', max_length=512, unique=True)
    title = models.CharField(verbose_name='Название площадки', max_length=512)
    type = models.CharField(verbose_name='Тип площадки', max_length=30, choices=SITE_TYPES)
    
    def __str__(self):
        return str(self.url)
    
    class Meta:
        verbose_name = 'Площадка для наблюдения'
        verbose_name_plural = 'Площадки для наблюдения'
    