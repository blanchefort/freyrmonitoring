from django.template.response import TemplateResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from core.models.theme import Theme, ThemeArticles
from core.models.article import Article

def index(request):
    """Стартовая страница
    """
    themes = []
    for theme in Theme.objects.all().order_by('-id'):
        t = {}
        t['id'] = theme.id
        t['name'] = theme.name
        earliest = ThemeArticles.objects.filter(theme_link=theme).order_by('article_link__publish_date')[0]
        t['start'] = Article.objects.get(id=earliest.article_link.id).publish_date
        latest =  ThemeArticles.objects.filter(theme_link=theme).order_by('-article_link__publish_date')[0]
        t['end'] = Article.objects.get(id=latest.article_link.id).publish_date
        t['article_count'] = ThemeArticles.objects.filter(theme_link=theme).count()
        t['comment_count'] = 0
        pos, neg, likes = 0, 0, 0
        for item in ThemeArticles.objects.filter(theme_link=theme):
            item = Article.objects.get(id=item.article_link.id)
            if item.sentiment == 1:
                pos += 1
            if item.sentiment == 2:
                neg += 1
            likes += item.likes
        t['likes_count'] = likes
        t['warning'] = neg >= pos
        themes.append(t)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Кластеры событий',
        'themes': themes,
    }
    return TemplateResponse(request, 'events.html', context=context)

def info(request, event_id):
    """Информация о кластере
    """

    # Основная информация о кластере
    theme = Theme.objects.get(id=event_id)
    theme_links = ThemeArticles.objects.filter(theme_link=theme)
    neutral_count = 0
    positive_count = 0
    negative_count = 0
    articles = []
    for link in theme_links:
        article = Article.objects.get(id=link.article_link.id)
        articles.append(article)
        if article.sentiment == 0:
            neutral_count += 1
        elif article.sentiment == 1:
            positive_count += 1
        elif article.sentiment == 2:
            negative_count += 1
    context = {
        'title': 'FreyrMonitoring',
        'page_title': theme.name,
        'articles': articles,
        'articles_neutral_count': neutral_count,
        'articles_positive_count': positive_count,
        'articles_negative_count': negative_count,
    }

    # График: хронология публикаций
    days = []
    counts = []
    for item in Article.objects\
        .filter(article_themes__theme_link=theme)\
        .annotate(day=TruncDay('publish_date'))\
        .order_by('publish_date')\
        .values('day')\
        .annotate(count=Count('id', distinct=True))\
        .values('day', 'count'):
        if item['day'] in days:
            counts[days.index(item['day'])] += item['count']
        else:
            days.append(item['day'])
            counts.append(item['count'])
    
    context.update({'chronology': [{'day': d, 'count': c} for d, c in zip(days, counts)]})

    # Начало и конец кластера
    earliest = ThemeArticles.objects.filter(theme_link=theme).order_by('article_link__publish_date')[0]
    context.update({'cluster_start': Article.objects.get(id=earliest.article_link.id).publish_date})
    latest =  ThemeArticles.objects.filter(theme_link=theme).order_by('-article_link__publish_date')[0]
    context.update({'cluster_end': Article.objects.get(id=latest.article_link.id).publish_date})

    # Количество статей
    context.update({'cluser_articles': ThemeArticles.objects.filter(theme_link=theme).count()})
    # Количество лайков
    context.update({'cluser_likes': Article.objects\
        .filter(article_themes__theme_link=theme)\
        .aggregate(sum=Sum('likes'))['sum']})
    # Количество комментариев
    context.update({'cluser_comments': 0})

    # Распределение по типу источника
    source_types = {
        'site': 'Отдельный сайт',
        'kp': 'Комсомольская правда',
        'mk': 'Московский комсомолец',
        'kommersant': 'Коммерсант',
        'vesti': 'Вести',
        'odnoklassniki_domain': 'Одноклассники',
        'odnoklassniki_id': 'Одноклассники',
        'insta': 'Инстаграм',
        'telega': 'Телеграм',
        'vk_domain': 'Вконтакте',
        'vk_owner': 'Вконтакте',
        'youtube': 'Ютуб',
        'twi': 'Твиттер',
        'facebook': 'Фейсбук',
        'viber': 'Вайбер',
        'whatsapp': 'Вотсап',
        'tiktok': 'Тик-Ток',
        'yandex': 'Яндекс.Район',
    }
    source_name, source_count = [], []
    for item in ThemeArticles.objects.filter(theme_link=theme):
        stype = Article.objects.get(pk=item.article_link.id).site.type
        if stype in source_name:
            source_count[source_name.index(stype)] += 1
        else:
            source_name.append(stype)
            source_count.append(1)
    context.update({
        'source_name': [source_types[s] for s in source_name],
        'source_count': source_count,
    })
    return TemplateResponse(request, 'event_page.html', context=context)