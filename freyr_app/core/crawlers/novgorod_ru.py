from .freyr_crawler import FreyrCrawler
from dateutil import parser
import re

class NovgorodRuCrawler(FreyrCrawler):
    def __init__(self):
        super(NovgorodRuCrawler, self).__init__()
        self.domain = 'novgorod.ru'
    
    def latest_posts(self):
        """Получаем последные статьи
        """
        items = []
        response = self.session.get('https://news.novgorod.ru/news/')
        if response.status_code != 200:
            return items
        self._collect_external_links(response)
        links_to_download = [l for l in response.html.absolute_links 
                             if '/news/' in l and '/licence/' not in l]
        for link in links_to_download:
            response = self.session.get(link)
            if response.status_code == 200:
                self._collect_external_links(response)
                items.append({
                    'url': link,
                    'title': response.html.find('h1', first=True).text,
                    'text': response.html.find('.news-text-col', first=True).text,
                    'date': parser.parse(response.html.find('time', first=True).attrs['datetime']),
                    'views': response.html.find('.news-header-3', first=True).text,
                })
        return items
    
    def latest_comments(self, url):
        """Получаем последные комментарии
        """
        items = []
        post_id = re.findall( r'\d+', url)
        if len(post_id) == 0:
            return items
        url = 'https://news.novgorod.ru/news/comments/' + post_id[-1] + '/'
        response = self.session.get(url)
        if response.status_code == 200:
            self._collect_external_links(response)
            if response.html.find('.caq_container', first=True) and response.html.find('.caq_container', first=True).find('.caq_comment'):
                comment_blocks = response.html.find('.caq_container', first=True).find('.caq_comment')
                for comment in comment_blocks:
                    if comment.find('.caq_comment_body', first=True):
                        items.append({
                            'url': url,
                            'username': comment.find('.username', first=True).text,
                            'system_id': int(comment.find('.caq_comment_body', first=True).attrs['data-id']),
                            'text': comment.find('.caq_comment_body', first=True).text,
                            'likes': int(comment.find('.vote_up_result', first=True).text.replace('+', '')),
                            'dislikes': int(comment.find('.vote_down_result', first=True).text.replace('-', ''))
                        })
        return items