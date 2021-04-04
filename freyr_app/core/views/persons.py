from datetime import date, timedelta
from django.template.response import TemplateResponse
from django.core.paginator import Paginator
from core.models.entity import Entity, EntityLink
from core.models.article import Article
from core.processing.calculate_indexes import calculate_nps_int, nps_norm100


def index(request):
    """Стартовая страница
    """
    persons = Entity.objects.filter(type='PER')
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Выявленные персоны',
        'items': persons,
        'item_link': '/persons/',
        'autocomplete': True,
    }
    return TemplateResponse(request, 'persons.html', context=context)


def person_page(request, ent_id):
    """Страница сущности
    """
    entity = Entity.objects.get(id=ent_id)
    # totalStat
    days = []
    counts_positive = []
    counts_neutral = []
    counts_negative = []
    for i in range(30, 0, -1):
        day = date.today() - timedelta(days=i)
        days.append(day.strftime('%d.%m.%y'))
        counts_positive.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__publish_date__date=day).filter(sentiment=1).count())
        counts_neutral.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__publish_date__date=day).filter(sentiment=0).count())
        counts_negative.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__publish_date__date=day).filter(sentiment=2).count())

    articles = Article.objects.filter(article_entities__entity_link=entity)
    articles = articles.distinct()
    paginator = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    page = int(request.GET.get('page', 0))
    if page < 3:
        page_range = paginator.page_range[:page+3]
    else:
        page_range = paginator.page_range[page-3:page+3]
    
    # Индекс лояльности
    neu = EntityLink.objects.filter(entity_link=entity).filter(sentiment=0).count()
    pos = EntityLink.objects.filter(entity_link=entity).filter(sentiment=1).count()
    neg = EntityLink.objects.filter(entity_link=entity).filter(sentiment=2).count()
    context = {
        'title': 'FreyrMonitoring',
        'page_title': entity.name,
        'articles': articles,
        'paginator': paginator,
        'page_range': page_range,
        'positive_count': pos,
        'neutral_count': neu,
        'negative_count': neg,

        'days': days,
        'counts_positive': counts_positive,
        'counts_neutral': counts_neutral,
        'counts_negative': counts_negative,
    }

    loyalty_index = nps_norm100(calculate_nps_int(pos, neg, neu))
    context.update({'loyalty_index': loyalty_index})
    if loyalty_index <= 25:
        context.update({'loyalty_type': 'bad'})
    elif loyalty_index >= 55:
        context.update({'loyalty_type': 'good'})
    else:
        context.update({'loyalty_type': 'nono'})
    
    # индекс значимости (влиятельности) 
    # - процент сообщений о персоне к общему количеству сообщений
    total = EntityLink.objects.filter(entity_link__type='PER').count() + 1e-8
    person_mentions = EntityLink.objects.filter(entity_link=entity).count()
    significance_index = person_mentions / total
    significance_index *= 100
    context.update({'significance_index': significance_index})
    return TemplateResponse(request, 'person_page.html', context=context)
