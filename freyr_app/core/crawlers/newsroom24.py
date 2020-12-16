import datetime
from requests_html import HTMLSession
from purl import URL
import datetime

def get_newsroom24():
    session = HTMLSession()
    links = ['https://newsroom24.ru/archive/',
             'https://newsroom24.ru/archive/?PAGEN_1=2',
             'https://newsroom24.ru/archive/?PAGEN_1=3']
    absolute_links = []
    for lnk in links:
        request = session.get(lnk)
        if request.status_code != 200:
            continue
        absolute_links += request.html.absolute_links
    links_to_download = []
    items = []
    for lnk in absolute_links:
        if 'newsroom24.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['zhizn', 'business', 'glaz', 'kontekst', 
                'opinions', 'photo', 'sport', 'details',
                'nocomments', 'criminal', 'technologies']
            if url.path_segment(1) in segments and url.path_segment(2) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        request = session.get(lnk)
        meta_block = request.html.find('.news_big_photo', first=True)
        date = meta_block.find('.date', first=True).text
        date = datetime.datetime.strptime(date, "%d.%m.%Y %H:%M")
        items.append({
            'url': lnk,
            'title': request.html.find('h1', first=True).text,
            'date': date,
            'text': request.html.find('.detail_news', first=True).text,
        })
    return items