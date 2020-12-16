from datetime import datetime
from requests_html import HTMLSession
from purl import URL
import datetime

def get_pravdann():
    session = HTMLSession()
    r = session.get('https://pravda-nn.ru/')
    links_to_download = []
    items = []
    if r.status_code != 200:
        return items
    for lnk in r.html.absolute_links:
        if 'pravda-nn.ru' == URL.from_string(lnk).host():
            url = URL.from_string(lnk)
            if url.path_segment(0) == 'news' and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        r = session.get(lnk)
        date = r.html.find('.article__time', first=True).text
        items.append({
                'url': lnk,
                'title': r.html.find('.article__title', first=True).text,
                'date': datetime.datetime.strptime(date, "%H:%M, %d/%m/%Y"),
                'text': r.html.find('.article__content', first=True).text,
            })
    return items