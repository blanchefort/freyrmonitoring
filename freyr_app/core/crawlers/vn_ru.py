from .freyr_crawler import FreyrCrawler
from purl import URL
import datetime

class VNRuCrawler(FreyrCrawler):
    def __init__(self):
        super(VNRuCrawler, self).__init__()
        self.domain = 'vnru.ru'
        
    def latest_posts(self):
        """Получаем последные статьи
        """
        items = []
        response = self.session.get('https://vnru.ru/news.html')
        if response.status_code != 200:
            return items
        self._collect_external_links(response)
        links_to_download = []
        for link in response.html.absolute_links:
            url = URL(link)
            if url.path_segment(0) in ['news', 'korotkoj-strokoj'] and not link.endswith('#comments'):
                links_to_download.append(link)
        for link in links_to_download:
            response = self.session.get(link)
            if response.status_code == 200:
                self._collect_external_links(response)
                if response.html.find('.article', first=True):
                    date = response.html.find('.article__date', first=True).text
                    date = self._format_date(date)
                    article = response.html.find('.article', first=True)
                    statistics = article.find('.article-head', first=True).find('div.icons', first=True)
                    items.append({
                        'url': link,
                        'title': response.html.find('h1', first=True).text,
                        'text': article.find('.article-text', first=True).text,
                        'date': date,
                        'views': statistics.find('div.icon__value')[0].text,
                        'likes': article.find('.article-share__like', first=True).text,
                    })
        return items
        
    async def latest_comments(self, url):
        """Получаем последные комментарии
        """
        items = []
        link = url + '#comments'
        response = await self.asession.get(link)
        if response.status_code == 200:
            self._collect_external_links(response)
            await response.html.arender()
            comments_block = response.html.find('.ajax-wrapper.comments-wrapper.uk-margin-medium-bottom', first=True)
            if comments_block:
                comments = comments_block.find('.comment')
                for comment in comments:
                    date = comment.find('.comment__date', first=True).text
                    date = date.replace('\xa0', '')
                    date = datetime.datetime.strptime(date, "%d.%m.%Y %H:%M")
                    items.append({
                        'url': url,
                        'username': comment.find('.comment__name', first=True).text,
                        'system_id': int(date.timestamp()),
                        'text': comment.find('.comment__text', first=True).text,
                    })
        return items
                
    
    def _format_date(self, date):
        """Нормализуем дату
        """
        months = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
                  'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10',
                  'ноября': '11', 'декабря': '12',}
        date = date.replace('\xa0', '')
        for item in months:
            date = date.lower().replace(item, months[item])
        date = datetime.datetime.strptime(date, "%d %m %Y %H:%M")
        return date