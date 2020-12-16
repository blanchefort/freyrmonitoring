from requests_html import HTMLSession
from purl import URL
from dateutil import parser

def get_koza():
    session = HTMLSession()
    r = session.get('https://koza.press/')
    links_to_download = []
    items = []
    if r.status_code != 200:
        return items
    for lnk in r.html.absolute_links:
        if 'koza.press' == URL.from_string(lnk).host():
            url = URL.from_string(lnk)
            if url.path_segment(0) == 'news' and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        r = session.get(lnk)
        items.append({
                'url': lnk,
                'title': r.html.find('.main-post-title', first=True).text,
                'date': parser.parse(r.html.find('.main-post-date', first=True).text),
                'text': r.html.find('.main-post-article', first=True).text,
            })
    return items