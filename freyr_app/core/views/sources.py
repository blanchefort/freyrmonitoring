from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.forms import AddUrlForm
from core.models.site import Site
from core.processing.url import process_url
from core.crawlers import VKParser

def index(request):
    """Стартовая страница
    """
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Интернет-ресурсы',
        'sources': Site.objects.all(),
#         'article_count': article_collector(),
    }
    return TemplateResponse(request, 'sources/list.html', context=context)

@login_required
def add_source(request):
    """Добавляем новую площадку
    """
    context = {
        'title': 'FreyrMonitoring',
        'page_title': 'Интернет-ресурсы: Добавляем новую площадку',
    }

    if request.method == 'POST':
        form = AddUrlForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if Site.objects.filter(url=url).count() > 0:
                messages.add_message(request, messages.INFO, 'Такая ссылка уже есть в индексе.')
            else:
                url_type, link = process_url(url)
                if url_type == 'site':
                    messages.add_message(request, messages.INFO, 'Ссылка на распознана или ей требуется индивидуальный парсер. Обратитесь за этим к разработчикам.')
                elif url_type.startswith('vk_'):
                    vk = VKParser()
                    info = vk.get_group_info_by_url(link)
                    if info['is_closed'] > 0:
                        messages.add_message(request, messages.INFO, 'Это закрытое сообщество. Сбор информации будет осуществляться, если сервисный аккаунт имеет доступ к данному сообществу.')
                    context.update({
                        'url': link,
                        'title': info['name'],
                        'type': url_type,
                        'show_info': True,
                    })
                else:
                    messages.add_message(request, messages.INFO, '234324')
    else:
        context.update({'form': AddUrlForm()})
            
    
    return TemplateResponse(request, 'sources/add.html', context=context)