from django.template.response import TemplateResponse
from core.models.entity import Entity, EntityLink
from core.models.article import Article
from django.db.models import Count
from datetime import date, timedelta

def index(request):
    """Стартовая страница
    """
    ents = []
    objs = Entity.objects.filter(type='PER')
    for e in objs:
        if EntityLink.objects.filter(entity_link=e).count() >= 5:
            ents.append(e)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Выявленные персоны',
        'ents': ents,
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
    for i in range(7, 0, -1):
        day = date.today() - timedelta(days=i)
        days.append(day.strftime('%d.%m.%y'))
        counts_positive.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__theme=True).filter(article_link__publish_date__date=day).filter(article_link__sentiment=1).count())
        counts_neutral.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__theme=True).filter(article_link__publish_date__date=day).filter(article_link__sentiment=0).count())
        counts_negative.append(
            EntityLink.objects.filter(entity_link=entity).filter(article_link__theme=True).filter(article_link__publish_date__date=day).filter(article_link__sentiment=2).count())

    
    articles_links = EntityLink.objects.filter(entity_link=entity)
    neutral_count = 0
    positive_count = 0
    negative_count = 0
    articles = []
    for link in articles_links:
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
        'page_title': entity.name,
        'articles': articles,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_count': negative_count,

        'days': days,
        'counts_positive': counts_positive,
        'counts_neutral': counts_neutral,
        'counts_negative': counts_negative,
    }
    # Индекс лояльности
    total = EntityLink.objects.filter(entity_link=entity)\
        .filter(article_link__theme=True).count() + 1e-8
    pos = EntityLink.objects.filter(entity_link=entity)\
        .filter(article_link__theme=True).filter(article_link__sentiment=1).count()
    neg = EntityLink.objects.filter(entity_link=entity)\
        .filter(article_link__theme=True).filter(article_link__sentiment=2).count()
    loyalty_index = pos - neg
    loyalty_index /= total
    loyalty_index *= 100
    context.update({'loyalty_index': loyalty_index})
    if loyalty_index <= -26:
        context.update({'loyalty_type': 'bad'})
    elif loyalty_index >= 26:
        context.update({'loyalty_type': 'good'})
    else:
        context.update({'loyalty_type': 'nono'})
    
    # индекс значимости (влиятельности) 
    # - процент сообщений о персоне к общему количеству сообщений
    total = Article.objects.filter(theme=True).count() + 1e-8
    person_mentions = EntityLink.objects.filter(entity_link=entity).count()
    significance_index = person_mentions / total
    significance_index *= 100
    context.update({'significance_index': significance_index})
    return TemplateResponse(request, 'person_page.html', context=context)
    