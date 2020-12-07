from django.template.response import TemplateResponse
from core.models.entity import Entity, EntityLink
from core.models.article import Article
from django.db.models import Count

def index(request):
    """Стартовая страница
    """
    ents = []
    objs = Entity.objects.filter(type='ORG')
    for e in objs:
        if EntityLink.objects.filter(entity_link=e).count() >= 5:
            ents.append(e)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Выявленные организации',
        'ents': ents,
    }
    return TemplateResponse(request, 'orgs.html', context=context)

def org_page(request, ent_id):
    """Страница сущности
    """
    entity = Entity.objects.get(id=ent_id)
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
        'page_title': f'Организация: {entity.name}',
        'articles': articles,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
    }
    return TemplateResponse(request, 'entity_page.html', context=context)
    