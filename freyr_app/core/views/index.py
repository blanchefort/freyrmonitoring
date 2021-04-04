from datetime import date, timedelta
import configparser
from django.conf import settings
from django.template.response import TemplateResponse
from django.db.models import Count
from ..models import Article, Entity, EntityLink, Theme, ThemeArticles
from ..processing.calculate_indexes import nps_norm100, calculate_nps_int

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
    top_per, per_neutral_count, per_positive_count, per_negative_count = [], 0, 0, 0
    if Entity.objects.filter(type='PER').count() > 0:
        top_per = Entity.objects.filter(type='PER').annotate(total=Count('entity_articles')).order_by('-total')[0]
        per_neutral_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=0).count()
        per_positive_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=1).count()
        per_negative_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=2).count()
    
    # orgStat
    top_org, org_neutral_count, org_positive_count, org_negative_count = [], 0, 0, 0
    if Entity.objects.filter(type='ORG').count() > 0:
        top_org = Entity.objects.filter(type='ORG').annotate(total=Count('entity_articles')).order_by('-total')[0]
        org_neutral_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=0).count()
        org_positive_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=1).count()
        org_negative_count = EntityLink.objects.filter(entity_link=top_per).filter(sentiment=2).count()
    
    # TopCluster
    top_theme, theme_articles, theme_count = [], [], 0
    if Theme.objects.all().count() > 0:
        top_theme = Theme.objects.all().annotate(total=Count('theme_articles')).order_by('-total')[0]
        theme_articles = ThemeArticles.objects.filter(theme_link=top_theme).order_by('article_link__publish_date')
        theme_count = theme_articles.count()
        theme_articles = theme_articles[:5]

    # region_name
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': config['REGION']['NAME'],
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

    # Индекс лояльности
    neu = Article.objects.filter(theme=True).filter(sentiment=0).count() + 1e-8
    pos = Article.objects.filter(theme=True).filter(sentiment=1).count()
    neg = Article.objects.filter(theme=True).filter(sentiment=2).count()
    loyalty_index = nps_norm100(calculate_nps_int(pos, neg, neu))
    context.update({'loyalty_index': loyalty_index})
    if loyalty_index <= 25:
        context.update({'loyalty_type': 'bad'})
    elif loyalty_index >= 55:
        context.update({'loyalty_type': 'good'})
    else:
        context.update({'loyalty_type': 'nono'})
    return TemplateResponse(request, 'index.html', context=context)
