import vk_api
from typing import List, Optional, Tuple, Dict
from django.conf import settings
import configparser
import datetime

class VKParser:
    """Получаем информацию из ВК
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(settings.CONFIG_INI_PATH)
        self.session = vk_api.VkApi(token=config['VK']['TOKEN'])
        self.vk = self.session.get_api()
        self.vk_tools = vk_api.VkTools(self.session)
    
    def get_latest_posts(self, point: str = '', domain: bool = True) -> List:
        """Получаем 100 последних постов из сообщества
        
        Args:
            point - идентификатор сообщества - domain или owner_id
            domain - лаг о том, используется domain или owner_id
        """
        if domain == True:
            response = self.vk.wall.get(domain=point, count=100)
        else:
            response = self.vk.wall.get(owner_id=point, count=100)
        result = []
        for item in response['items']:
            if len(item['text']) > 0: 
                result.append({
                    'id': item['id'],
                    'date': datetime.datetime.fromtimestamp(item['date']),
                    'owner_id': item['owner_id'],
                    'comments': item['comments']['count'] or 0,
                    'likes': item['likes']['count'] or 0,
                    'reposts': item['reposts']['count'] or 0,
                    'views': item['views']['count'] or 0,
                    'text': item['text'],
                    'url': self.post2url(item['id'], item['owner_id'])
                })
        return result

    def get_post_comments(self, owner_id: int, post_id: int) -> List:
        """Получаем все комментарии к посту
        
        Args:
            owner_id - идентификатор хозяина поста
            post_id - идентификатор поста
        """
        response = self.vk_tools.get_all_slow(
            'wall.getComments',
            max_count=75,
            values={'owner_id': owner_id, 'post_id': post_id})
        result = []
        for item in response['items']:
            result.append({
                'date': datetime.datetime.fromtimestamp(item['date']),
                'from_id': item.get('from_id', None),
                'text': item.get('text', 'Without text')
            })
        return result
    
    def get_users(self, user_ids: List) -> List:
        """Получаем информацию на список пользователей по id.
        Не более 1000 шт.
        
        Args:
            user_ids - список идентификаторов пользователей
        """
        users_line = ''
        for uid in user_ids:
            users_line += str(uid) + ','
        response = self.vk.users.get(user_ids=users_line, fields='sex,city')
        result = []
        for item in response:
            result.append({
                item['id']: {
                    'sex': item.get('sex', None),
                    'city': item.get('city', None),
                }
            })
        return result
    
    def url2domain(self, link: str) -> Tuple:
        """Переводим веб-ссылку в домен ВК с указанием его типа

        Args:
            link (str): Ссылка. Например, https://vk.com/ul

        Returns:
            Tuple: домен, по которому осуществлять запрос, 
                    True - если тип `domain`, False - если тип `owner_id`
        """
        domain = link.split('vk.com/')[1]
        if len(domain.split('public')) == 2 and domain.split('public')[1].isdigit():
            return -int(domain.split('public')[1]), False
        return domain, True
    
    def post2url(self, post_id: int, owner_id: int) -> str:
        """Формируем ссылку на пост

        Args:
            post_id (int): Идентификатор поста
            owner_id (int): Идентификатор хозяина поста

        Returns:
            str: Ссылка на пост
        """
        owner_id = -owner_id
        return f'https://vk.com/feed?w=wall-{owner_id}_{post_id}'
    
    def url2post(self, url: str) -> Tuple:
        """Переводим ссылку на пост в его идентификаторы

        Args:
            url (str): Полная валидная ссылка на пост

        Returns:
            Tuple: owner_id, post_id
        """
        data = url.split('https://vk.com/feed?w=wall-')[1]
        owner_id, post_id = data.split('_')
        owner_id = -int(owner_id)
        post_id = int(post_id)
        return owner_id, post_id
    
    def get_group_info_by_url(self, link: str) -> Dict:
        """Получаем информацию о сообществе

        Args:
            group_id (Optional): идентификатор сообщества или его домен

        Returns:
            Dict: [description]
        """
        domain, _ = self.url2domain(link)
        if type(domain) == int:
            domain = str(-domain)
        response = self.vk.groups.getById(group_id=domain, fields='description')
        return {
            'name': response[0].get('name', None),
            'id': response[0].get('id', None),
            'screen_name': response[0].get('screen_name', None),
            'is_closed': response[0].get('is_closed', None),
            'description': response[0].get('description', None),
        }