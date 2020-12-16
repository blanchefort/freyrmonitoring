from requests_html import HTMLSession
from purl import URL
import datetime
from newspaper import Article

def get_newsnn():
    # TODO: не всегда скачивается полный текст статьи
    session = HTMLSession()
    r = session.get('https://newsnn.ru/')
    links_to_download = []
    items = []
    if r.status_code != 200:
        return items
    for lnk in r.html.absolute_links:
        if 'newsnn.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['article', 'cards', 'news']
            if url.path_segment(0) in segments:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        url = URL.from_string(lnk)
        date = url.path_segment(2)
        if date is not None and len(date) == 10:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': datetime.datetime.strptime(date, "%d-%m-%Y"),
                'text': a.text,
            })
    return items