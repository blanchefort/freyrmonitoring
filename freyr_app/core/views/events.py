from django.template.response import TemplateResponse
from core.models.theme import Theme, ThemeArticles
from core.models.article import Article

def index(request):
    """Стартовая страница
    """
    themes = Theme.objects.all()
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Кластеры событий',
        'themes': themes,
    }
    return TemplateResponse(request, 'events.html', context=context)

def info(request, event_id):
    """Информация о кластере
    """
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
        'page_title': f'Кластер: {theme.name}',
        'articles': articles,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
    }
    return TemplateResponse(request, 'entity_page.html', context=context)