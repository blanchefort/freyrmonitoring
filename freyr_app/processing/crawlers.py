"""Методы получения материалов с площадок
"""
from datetime import datetime, timedelta
from requests_html import HTMLSession
from requests_html import AsyncHTMLSession
from purl import URL
from dateutil import parser
from newspaper import Article
from instagram import Account, Media, WebAgent, Comment

# Специальные методы для сайтов заказчика
# сломался
def get_newsroom24():
    session = HTMLSession()
    links = ['https://newsroom24.ru/archive/',
             'https://newsroom24.ru/archive/?PAGEN_1=2',
             'https://newsroom24.ru/archive/?PAGEN_1=3']
    absolute_links = []
    for lnk in links:
        request = session.get(lnk)
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
        items.append({
            'url': lnk,
            'title': request.html.find('h1', first=True).text,
            'date': parser.parse(request.html.find('.date_time', first=True).text),
            'text': request.html.find('.detail_news', first=True).text,
        })
    return items

def get_vgoroden():
    # Нужен обход несколько раз в день
    session = HTMLSession()
    request = session.get('https://www.vgoroden.ru/')
    links_to_download = []
    items = []
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
            title = request.html.find('h1', first=True).text
            date = date.text
            date = date.split('Сегодня, ')[1]
            date = parser.parse(date)
            article = request.html.find('article')
            text = article[0].find('div')[10].text
            items.append({
                'url': lnk,
                'title': title,
                'date': date,
                'text': text,
            })
    return items

def get_newsnn():
    # TODO: не всегда скачивается полный текст статьи
    # Замечены некорректные даты
    session = HTMLSession()
    r = session.get('https://newsnn.ru/')
    links_to_download = []
    items = []
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
                'date': parser.parse(date),
                'text': a.text,
            })
    return items

def get_progorodnn():
    # TODO: Убрать комменты, чтобы ссылки не дублировались
    # #comments убрать #commentform - убрать
    # https://progorodnn.ru/news/90079#comments
    # Месяц и дата иногда путаются
    link = 'https://progorodnn.ru/news'
    session = HTMLSession()
    r = session.get(link)
    items = []
    links_to_download = []
    for lnk in r.html.absolute_links:
        if 'progorodnn.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['afisha', 'announcement', 'articles', 'auto', 'comnews', 'news', 'newspapers',
                        'peoplecontrol', 'trud']
            if url.path_segment(0) in segments and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        url = URL.from_string(lnk)
        request = session.get(lnk)
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
            date = parser.parse(date)
            items.append({
                    'url': lnk,
                    'title': title,
                    'date': date,
                    'text': text,
                })
    return items

def get_nnnow():
    session = HTMLSession()
    r = session.get('https://nn-now.ru/')
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if 'nn-now.ru' in lnk:
            url = URL.from_string(lnk)
            segments = ['2020', 'author', 'category', 'contacts', 'dk', 'home', 'page', 'share.php', 'tag', 'vyiboryi']
            if url.path_segment(0) not in segments and url.path_segment(0) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        if len(a.text) > 0:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

def get_pravdann():
    # TODO: Иногда путается день и месяц
    session = HTMLSession()
    r = session.get('https://pravda-nn.ru/')
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if 'pravda-nn.ru' == URL.from_string(lnk).host():
            url = URL.from_string(lnk)
            if url.path_segment(0) == 'news' and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        r = session.get(lnk)
        items.append({
                'url': lnk,
                'title': r.html.find('.article__title', first=True).text,
                'date': parser.parse(r.html.find('.article__time', first=True).text),
                'text': r.html.find('.article__content', first=True).text,
            })
    return items

def get_koza():
    session = HTMLSession()
    r = session.get('https://koza.press/')
    links_to_download = []
    items = []
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

def get_opennov():
    session = HTMLSession()
    r = session.get('https://opennov.ru/news')
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if 'opennov.ru' == URL.from_string(lnk).host():
            url = URL.from_string(lnk)
            if url.path_segment(0) == 'news' and url.path_segment(1) is not None \
            and url.path_segment(2) is not None and url.path_segment(3) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

# Общие методы
def get_standalone_site(link):
    items = []
    return items

def get_kp(link):
    """link='https://www.nnov.kp.ru/'
    """
    url = URL.from_string(link)
    session = HTMLSession()
    r = session.get(link)
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if url.host() in lnk:
            url = URL.from_string(lnk)
            segments = ['action', 'afisha', 'daily', 'dom', 'economics', 'health', 'incidents', 'online', 'photo',
                        'politics', 'radio', 'society', 'sport', 'stars', 'subscribe', 'tourism', 'video']
            if url.path_segment(0) in segments and url.path_segment(2) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        if a.publish_date is not None:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

def get_mk(link):
    """link='https://nn.mk.ru/news/'
    """
    url = URL.from_string(link)
    session = HTMLSession()
    r = session.get(link)
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if url.host() in lnk:
            url = URL.from_string(lnk)
            segments = ['culture', 'economics', 'incident', 'news', 'politics', 'science', 'social','sport',]
            if url.path_segment(0) in segments and url.path_segment(1) is not None and url.path_segment(2) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        if a.publish_date is not None:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

def get_kommersant(link):
    """link='https://www.kommersant.ru/regions/52'
    """
    url = URL.from_string(link)
    session = HTMLSession()
    r = session.get(link)
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if url.host() in lnk:
            url = URL.from_string(lnk)
            if url.path_segment(0) == 'doc' and ('from' in url.query()) is False:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        if len(a.text) > 0:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

def get_vesti(link):
    """link='https://vestinn.ru/news/'
    """
    url = URL.from_string(link)
    session = HTMLSession()
    r = session.get(link)
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if url.host() in lnk:
            url = URL.from_string(lnk)
            if 'news' == url.path_segment(0) and url.path_segment(1) is not None:
                links_to_download.append(lnk)
    for lnk in links_to_download:
        a = Article(lnk, language='ru')
        a.download()
        a.parse()
        if len(a.text) > 0:
            items.append({
                'url': lnk,
                'title': a.title,
                'date': a.publish_date,
                'text': a.text,
            })
    return items

def odnoklassniki_domain(group_domain):
    session = HTMLSession()
    r = session.get(f'https://ok.ru/{group_domain}')
    links_to_download = []
    items = []
    for lnk in r.html.absolute_links:
        if 'ok.ru' in URL.from_string(lnk).host():
            url = URL.from_string(lnk)
            if url.path_segment(0) == group_domain and url.path_segment(1) == 'topic':
                links_to_download.append(lnk)
    for lnk in links_to_download:
        r = session.get(lnk)
        date = r.html.find('.ucard_add-info_i')[0].text
        date_format = '%d.%m.%Y'
        if 'вчера' in date.lower():
            date = (datetime.now() - timedelta(days=1)).strftime(date_format) + ' ' + date.lower().split('вчера ')[1]
        elif 'сегодня' in date.lower():
            date = date.lower().split('сегодня ')[1]
        else:
            continue
        date = parser.parse(date)
        items.append({
                'url': lnk,
                'title': '',
                'date': date,
                'text': r.html.find('.__full')[1].text,
            })
    return items

def get_insta(account):
    '''Installation: https://github.com/OlegYurchik/pyInstagram
    '''
    agent = WebAgent()
    account = Account(account)
    media, pointer = agent.get_media(account)
    items = []
    for m in media:
        comments, _ = agent.get_comments(m)
        items.append({
            'comments': [Comment(c).text for c in comments],
            'text': m.caption,
            'likes': m.likes_count,
            'date': datetime.fromtimestamp(m.date),
        })
    return items
