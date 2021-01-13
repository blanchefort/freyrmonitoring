from django.template.response import TemplateResponse
from core.models import Category

def index(request):
    """Индекс счастья региона
    """
    context = {
        'page_title': 'Индекс удовлетворённости жизнью',
        'categories': Category.objects.all(),
    }
    return TemplateResponse(request, 'happiness.html', context=context)