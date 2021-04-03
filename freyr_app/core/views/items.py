import datetime
from django.template.response import TemplateResponse
from django.core.paginator import Paginator
from ..models.article import Article
from ..processing.calculate_indexes import loyalty_index
from ..forms import SearchItem
from core.processing.search import FaissSearch

def index(request):
    """Стартовая страница
    """
    today = datetime.datetime.now()
    earliest = Article.objects.filter(theme=True).order_by('publish_date')[0]
    oldest = Article.objects.filter(theme=True).order_by('-publish_date')[0]
    year_range = range(earliest.publish_date.year, oldest.publish_date.year+1)
    month = today.month
    year = today.year

    if request.method == 'GET':
        if int(request.GET.get('month', -1)) in range(1, 13):
            month = int(request.GET.get('month'))
        if int(request.GET.get('year', -1)) in year_range:
            year = int(request.GET.get('year'))

    articles = Article.objects.filter(theme=True)\
        .filter(publish_date__year=year, publish_date__month=month)\
        .order_by('-publish_date')
    neutral_count = Article.objects.filter(theme=True)\
        .filter(publish_date__year=year, publish_date__month=month)\
        .filter(sentiment=0).count()
    positive_count = Article.objects.filter(theme=True)\
        .filter(publish_date__year=year, publish_date__month=month)\
        .filter(sentiment=1).count()
    negative_count = Article.objects.filter(theme=True) \
        .filter(publish_date__year=year, publish_date__month=month)\
        .filter(sentiment=2).count()

    loyalty = loyalty_index(year, month)

    paginator = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    page = int(request.GET.get('page', 0))
    if page < 3:
        page_range = paginator.page_range[:page+3]
    else:
        page_range = paginator.page_range[page-3:page+3]
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Индекс лояльности',
        'articles': articles,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'year_range': year_range,
        'selected_month': month,
        'selected_year': year,
        'loyalty': loyalty,
        'paginator': paginator,
        'page_range': page_range,
    }
    return TemplateResponse(request, 'items.html', context=context)


def search(request):
    """Поиск по всем материалам
    """
    form = SearchItem()
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Поиск по проиндексированным материалам',
        'form': form,
    }

    if request.method == 'POST':
        search_query = request.POST.get('search_query')
        searcher = FaissSearch()
        if searcher.index:
            dist, ids = searcher.search(search_query)
            search_results = [Article.objects.get(search_idx=idx) for idx, d in zip(ids[0], dist[0]) if d > 0.02]

            context.update({'search_results': search_results})
            context.update({'search_query': search_query})
    
    return TemplateResponse(request, 'search.html', context=context)
