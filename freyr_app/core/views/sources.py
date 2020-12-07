from django.template.response import TemplateResponse
from core.forms import SiteForm
from core.models.site import Site


def index(request):
    """Стартовая страница
    """
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Интернет-ресурсы',
        'form': SiteForm(),
        'sources': Site.objects.all(),
#         'article_count': article_collector(),
    }
    return TemplateResponse(request, 'sources.html', context=context)

def add_site(request):
    """Добавляем новую площадку
    """
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Интернет-ресурсы: Добавляем новую площадку',
        'form': SiteForm(),
    }
    return TemplateResponse(request, 'sources.html', context=context)