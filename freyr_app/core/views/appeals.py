from django.template.response import TemplateResponse
from ..models import Article

def index(request):
    """Сообщения, на которые следует обратить внимание"""
    if request.GET.get('nonrelevant'):
        Article.objects.filter(pk=request.GET.get('nonrelevant')).update(appeal=2)
    elif request.GET.get('watched'):
        Article.objects.filter(pk=request.GET.get('watched')).update(appeal=3)

    unwatched = Article.objects.filter(appeal=1).order_by('publish_date')
    if unwatched.count() > 0:
        context = {
            'title': 'FreyrMonitoring',
            'page_title': 'Обращения граждан',
            'unwatched_count': unwatched.count(),
            'item': unwatched[0],
        }
    else:
        # Нет непросмотренных сообщений
        context = {
            'title': 'FreyrMonitoring',
            'page_title': 'Обращения граждан',
        }
    return TemplateResponse(request, 'appeals.html', context=context)