import datetime
from requests_html import HTMLSession
from purl import URL
from dateutil import parser

def get_vgoroden():
    # Нужен обход несколько раз в день
    session = HTMLSession()
    request = session.get('https://www.vgoroden.ru/')
    links_to_download = []
    items = []
    if request.status_code != 200:
        return items
    for lnk in request.html.absolute_links:
        if 'vgoroden.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['novosti' , 'mesta' ,'gorod', 'zhizn']
            if url.path_segment(0) in segments:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        request = session.get(lnk)
        date = request.html.find('div.text-bolder', first=True)
        if date is not None and 'Сегодня' in date.text:
            date = date.text
            date = date.split('Сегодня, ')[1]
            date = parser.parse(date)
            
            title = request.html.find('h1', first=True).text
            article = request.html.find('article')
            text = article[0].find('div')[10].text
            items.append({
                'url': lnk,
                'title': title,
                'date': date,
                'text': text,
            })
        elif date is not None and 'Вчера' in date.text:
            date = date.text
            date = date.split('Вчера, ')[1]
            hour, minutes = date.split(':')
            post_time = datetime.time(int(hour), int(minutes))
            post_date = datetime.date.today() - datetime.timedelta(1)
            date = datetime.datetime.combine(post_date, post_time)
            
            title = request.html.find('h1', first=True).text
            article = request.html.find('article')
            text = article[0].find('div')[10].text
            items.append({
                'url': lnk,
                'title': title,
                'date': date,
                'text': text,
            })
    return items