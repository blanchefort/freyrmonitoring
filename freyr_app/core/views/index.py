from django.template.response import TemplateResponse
from core.models.article import Article
from core.models.entity import Entity, EntityLink
from core.models.theme import Theme, ThemeArticles
from django.db.models import Count
from datetime import date, timedelta


def index(request):
    """Стартовая страница
    """
    # totalStat
    days = []
    counts_positive = []
    counts_neutral = []
    counts_negative = []
    for i in range(7, 0, -1):
        day = date.today() - timedelta(days=i)
        days.append(day.strftime('%d.%m.%y'))
        counts_positive.append(
            Article.objects.filter(
            publish_date__date=day).filter(
            theme=True).filter(
            sentiment=1).count())
        counts_neutral.append(
            Article.objects.filter(
            publish_date__date=day).filter(
            theme=True).filter(
            sentiment=0).count())
        counts_negative.append(
            Article.objects.filter(
            publish_date__date=day).filter(
            theme=True).filter(
            sentiment=2).count())
    
    # personStat
    objs = Entity.objects.filter(type='PER')
    top_per = None
    top_count = 0
    for e in objs:
        if EntityLink.objects.filter(entity_link=e).count() > top_count:
            top_count = EntityLink.objects.filter(entity_link=e).count()
            top_per = e
    articles_links = EntityLink.objects.filter(entity_link=top_per)
    per_neutral_count = 0
    per_positive_count = 0
    per_negative_count = 0
    for link in articles_links:
        article = Article.objects.get(id=link.article_link.id)
        if article.sentiment == 0:
            per_neutral_count += 1
        elif article.sentiment == 1:
            per_positive_count += 1
        elif article.sentiment == 2:
            per_negative_count += 1
    
    # orgStat
    objs = Entity.objects.filter(type='ORG')
    top_org = None
    top_count = 0
    for e in objs:
        if e.name not in ('СМИ', 'ИА “НИЖНИЙ СЕЙЧАС'):
            if EntityLink.objects.filter(entity_link=e).count() > top_count:
                top_count = EntityLink.objects.filter(entity_link=e).count()
                top_org = e
    articles_links = EntityLink.objects.filter(entity_link=top_org)
    org_neutral_count = 0
    org_positive_count = 0
    org_negative_count = 0
    for link in articles_links:
        article = Article.objects.get(id=link.article_link.id)
        if article.sentiment == 0:
            org_neutral_count += 1
        elif article.sentiment == 1:
            org_positive_count += 1
        elif article.sentiment == 2:
            org_negative_count += 1
    
    # TopCluster
    objs = Theme.objects.all()
    top_theme = None
    theme_count = 0
    for e in objs:
        if ThemeArticles.objects.filter(theme_link=e).count() > theme_count:
            theme_count = ThemeArticles.objects.filter(theme_link=e).count()
            top_theme = e
    theme_articles = ThemeArticles.objects.filter(theme_link=top_theme).order_by('id')[:5]
    
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Сводка',
        'days': days,
        'counts_positive': counts_positive,
        'counts_neutral': counts_neutral,
        'counts_negative': counts_negative,
        'top_per': top_per,
        'per_neutral_count': per_neutral_count,
        'per_positive_count': per_positive_count,
        'per_negative_count': per_negative_count,
        'top_org': top_org,
        'org_neutral_count': org_neutral_count,
        'org_positive_count': org_positive_count,
        'org_negative_count': org_negative_count,
        'top_theme': top_theme,
        'theme_count': theme_count,
        'theme_articles': theme_articles,
    }

    return TemplateResponse(request, 'index.html', context=context)