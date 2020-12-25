from django.template.response import TemplateResponse
from core.models.article import Article
from django.core.paginator import Paginator

def index(request):
    """Стартовая страница
    """
    articles = Article.objects.filter(theme=True).order_by('-publish_date')
    neutral_count = Article.objects.filter(theme=True).filter(sentiment=0).count()
    positive_count = Article.objects.filter(theme=True).filter(sentiment=1).count()
    negative_count = Article.objects.filter(theme=True).filter(sentiment=2).count()
    
    paginator = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Статьи в индексе',
        'articles': articles,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
    }
    return TemplateResponse(request, 'items.html', context=context)