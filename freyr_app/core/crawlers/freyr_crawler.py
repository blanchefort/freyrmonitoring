from abc import ABC
from requests_html import HTMLSession, AsyncHTMLSession
from purl import URL


class FreyrCrawler(ABC):
    """Абстрактный класс для сбора и парсинга контента"""
    def __init__(self, *args, **kwargs):
        super(FreyrCrawler, self).__init__()
        self.session = HTMLSession()
        self.asession = AsyncHTMLSession()
        self.domain = ''
        self.external_links = set()
    
    def latest_posts(self):
        """Получаем последные статьи
        """
        pass
    
    def latest_comments(self, url):
        """Получаем последные комментарии
        """
        pass
    
    def _collect_external_links(self, response):
        """Сборщик внешних ссылок
        """
        for link in response.html.absolute_links:
            url = URL(link)
            if self.domain not in url.host():
                self.external_links.add(url.host())
