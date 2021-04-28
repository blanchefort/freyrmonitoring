from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import HttpResponseNotFound, JsonResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.core.paginator import Paginator
from excel_response import ExcelResponse
from ..models import Theme, ThemeArticles, ThemeMarkup, Article, Comment, Site


@login_required
def index(request):
    """Стартовая страница
    """
    themes = Theme.objects.all().order_by('-id')
    paginator = Paginator(themes, 10)
    page = request.GET.get('page')
    themes = paginator.get_page(page)
    themes2display = []
    for theme in themes:
        article_count = ThemeArticles.objects.filter(theme_link=theme).filter(article_link__theme=True).count()
        t = {'id': theme.id, 'name': theme.name}
        earliest = ThemeArticles.objects.filter(theme_link=theme).filter(article_link__theme=True).order_by(
            'article_link__publish_date')[0]
        t['start'] = Article.objects.get(pk=earliest.article_link.id).publish_date
        latest = ThemeArticles.objects.filter(theme_link=theme).filter(article_link__theme=True).order_by(
            '-article_link__publish_date')[0]
        t['end'] = Article.objects.get(pk=latest.article_link.id).publish_date
        t['article_count'] = article_count
        t['comment_count'] = 0
        pos, neg, likes = 0, 0, 0
        for item in ThemeArticles.objects.filter(theme_link=theme).filter(article_link__theme=True):
            item = Article.objects.get(pk=item.article_link.id)
            t['comment_count'] += Comment.objects.filter(article=item).count()
            if item.sentiment == 1:
                pos += 1
            if item.sentiment == 2:
                neg += 1
            if item.likes:
                likes += item.likes
        t['likes_count'] = likes
        t['warning'] = neg > pos
        themes2display.append(t)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Выявленные события',
        'themes': themes2display,
        'themes_orig': themes,
    }
    return TemplateResponse(request, 'events.html', context=context)


@login_required
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
        articles.append({
            'url': article.url,
            'sentiment': article.sentiment,
            'title': article.title,
            'id': article.id,
            'text': article.text,
            'publish_date': article.publish_date,
            'site': article.site,
            'likes': article.likes,
            'views': article.views,
            'comment_count': Comment.objects.filter(article=article).count(),
        })
        if article.sentiment == 0:
            neutral_count += 1
        elif article.sentiment == 1:
            positive_count += 1
        elif article.sentiment == 2:
            negative_count += 1
    context = {
        'title': 'FreyrMonitoring',
        'theme_id': theme.id,
        'page_title': theme.name,
        'articles': articles,
        'articles_neutral_count': neutral_count,
        'articles_positive_count': positive_count,
        'articles_negative_count': negative_count,
    }

    # График: хронология публикаций
    days = []
    counts = []
    for item in Article.objects \
            .filter(article_themes__theme_link=theme) \
            .annotate(day=TruncDay('publish_date')) \
            .order_by('publish_date') \
            .values('day') \
            .annotate(count=Count('id', distinct=True)) \
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
    latest = ThemeArticles.objects.filter(theme_link=theme).order_by('-article_link__publish_date')[0]
    context.update({'cluster_end': Article.objects.get(id=latest.article_link.id).publish_date})

    # Количество статей
    context.update({'cluser_articles': ThemeArticles.objects.filter(theme_link=theme).count()})
    # Количество лайков
    context.update({'cluser_likes': Article.objects \
                   .filter(article_themes__theme_link=theme) \
                   .aggregate(sum=Sum('likes'))['sum']})
    # Количество комментариев
    context.update({'cluser_comments': Comment.objects.filter(article__article_themes__theme_link=theme).count()})

    # Распределение по типу источника
    source_types = {i[0]: i[1] for i in Site.SITE_TYPES}

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


@login_required
def excelview(request, event_id):
    """Выборка по кластеру в виде эксель-файла

    Args:
        event_id (int): Идентификатор темы
    """
    try:
        theme = Theme.objects.get(pk=event_id)
        data = []
        sentiment_map = ('Нейтрально', 'Позитивно', 'Негативно')
        for item in ThemeArticles.objects.filter(theme_link=theme):
            data.append({
                'Дата публикации': item.article_link.publish_date,
                'Ссылка': item.article_link.url,
                'Заголовок': item.article_link.title,
                'Тип источника': item.article_link.site.type,
                'Отношение к власти': sentiment_map[item.article_link.sentiment],
                'Общая тональность': sentiment_map[item.article_link.happiness_sentiment],
                'Лайки': item.article_link.likes,
                'Просмотры': item.article_link.views,
                'Комментарии': Comment.objects.filter(article=item.article_link).count(),
            })
        return ExcelResponse(data, f'FreyrMonitoring: Выборка по теме {theme.name}')
    except Theme.DoesNotExist:
        return HttpResponseNotFound('Такая тема не найдена!')


@login_required
def suggest_alt_title(request):
    """Предложение альтернативного заголовка
    """
    try:
        pk = request.GET.get('id', None)
        alt_title = request.GET.get('alt_title', None)
        theme = Theme.objects.get(pk=pk)
        ThemeMarkup.objects.create(
            theme=theme,
            name=alt_title
        )
        return JsonResponse({'result': True})
    except Theme.DoesNotExist:
        return HttpResponseNotFound()
