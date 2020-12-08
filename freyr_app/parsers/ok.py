from typing import List, Dict, Tuple
from requests_html import HTMLSession
import datetime
import re

class OKParser:
    """Получаем информацию из Одноклассников
    """
    def __init__(self):
        self.session = HTMLSession()
    
    def get_latest_posts(self, public_link: str) -> List:
        """Получаем список ссылок на последние материалы паблика
        """
        request = self.session.get(public_link)
        return [link for link in request.html.absolute_links if '/topic/' in link]
    
    def get_post(self, full_link: str) -> Tuple:
        """Получаем пост, комментарии к нему и мета-информацию
        """
        post_data = {}
        comments = []
        request = self.session.get(full_link)
        post_data['url'] = full_link
        date_string = request.html.find('.ucard_add-info_i', first=True).text or None
        post_data['date'] = self.normalize_datetime(date_string)
        if request.html.find('.mlr_cnt'):
            content_box = request.html.find('.mlr_cnt', first=True)
            if content_box.find('.__full', first=True):
                post_data['text'] = content_box.find('.__full', first=True).text
                if len(post_data['text']) == 0:
                    post_data['text'] = 'Without text'
            else:
                post_data['text'] = 'Without text'
            
            for comment in request.html.find('.comments_lst', first=True).find('.comments_body'):
                date_string = comment.find('.comments_date', first=True).text or None
                comment_text = comment.find('.comments_text', first=True).text
                if len(comment_text) == 0:
                    comment_text = 'Without text'
                comments.append({
                    'author_name': comment.find('.comments_author', first=True).text or None,
                    'date': self.normalize_datetime(date_string),
                    'text': comment_text
                })
        return post_data, comments
    
    def normalize_datetime(self, date_string: str) -> datetime.datetime:
        """Приводим спарсенные даты к номальному виду

        Args:
            date_string (str): Строка с датой поста

        Returns:
            datetime.datetime: Результат
        """
        #TODO: надо бы проверить месяцы
        months = {
            'янв': 1,
            'фев': 2,
            'мар': 3,
            'апр': 4,
            'мая': 5,
            'июн': 6,
            'июл': 7,
            'авг': 8,
            'сен': 9,
            'окт': 10,
            'ноя': 11,
            'дек': 12,
        }
        date_result = datetime.datetime.now()
        if re.match(r'\d\d:\d\d', date_string):
            hour, minutes = date_string.split(':')
            post_time = datetime.time(int(hour), int(minutes))
            post_date = datetime.date.today()
            date_result = datetime.datetime.combine(post_date, post_time)
        if re.match(r'\d\d \w+', date_string):
            day, month = date_string.split(' ')
            date_result = datetime.datetime(
                datetime.date.today().year,
                months[month],
                int(day))
        if re.match(r'\w+ \d\d:\d\d', date_string):
            hour, minutes = date_string.split(' ')[1].split(':')
            post_time = datetime.time(int(hour), int(minutes))
            post_date = datetime.date.today() - datetime.timedelta(1)
            date_result = datetime.datetime.combine(post_date, post_time)
        return date_result