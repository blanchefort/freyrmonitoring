from requests_html import HTMLSession
from purl import URL
import datetime

def get_progorodnn():
    link = 'https://progorodnn.ru/news'
    session = HTMLSession()
    r = session.get(link)
    items = []
    if r.status_code != 200:
        return items
    links_to_download = []
    for lnk in r.html.absolute_links:
        if 'progorodnn.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['afisha', 'announcement', 'articles', 'auto', 'comnews', 'news', 'newspapers',
                        'peoplecontrol', 'trud']
            if url.path_segment(0) in segments and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        if lnk.endswith('#comments'):
            continue
        if lnk.endswith('#commentform'):
            continue
        url = URL.from_string(lnk)
        request = session.get(lnk)
        if request.status_code != 200:
            continue
        date = ''
        if url.path_segment(0) == 'peoplecontrol':
            date = request.html.find('.peoplecontrol-complaint__date', first=True).text
            title = request.html.find('a.breadcrumbs__item_link')[2].attrs['title']
            text = request.html.find('.peoplecontrol-complaint__text', first=True).text
        elif request.html.find('.article__date', first=True) is not None:
            date = request.html.find('.article__date', first=True).text
            title = request.html.find('.article__title', first=True).text
            text = request.html.find('.article__main', first=True).text
        months = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
                  'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10',
                  'ноября': '11', 'декабря': '12',}
        if date is not None and len(date) > 0:
            for item in months:
                date = date.lower().replace(item, months[item])
            try:
                date_formatted = datetime.datetime.strptime(date, "%d %m %Y")
            except:
                date_formatted = datetime.datetime.strptime(date, "%d %m %Y, %H:%M")
            items.append({
                    'url': lnk,
                    'title': title,
                    'date': date_formatted,
                    'text': text,
                })
    return items