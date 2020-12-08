from typing import List, Dict
from igramscraper.instagram import Instagram
import datetime
import configparser
from django.conf import settings

class InstaParser:
    """Получаем информацию из Инстаграма
    """

    def __init__(self, set_proxy: bool = False):
        config = configparser.ConfigParser()
        config.read(settings.CONFIG_INI_PATH)
        self.instagram = Instagram()
        # self.instagram.with_credentials(
        #     config['INSTA']['LOGIN'],
        #     config['INSTA']['PASSWORD'])
        # self.instagram.login()
        if set_proxy:
            # Нужно расширить список адресов, чтобы Инста не блокировала
            proxies = {
                'http': 'http://123.45.67.8:1087',
                'https': 'http://123.45.67.8:1087',
            }
            self.instagram.set_proxies(proxies)

    def get_account_info(self, account: str) -> Dict:
        """Мета-информация об аккаунте
        """
        account = self.instagram.get_account(account)
        return {
            'posts_count': account.media_count,
            'followers': account.followed_by_count,
            'follows': account.follows_count
        }
    
    def get_last_posts(self, account: str) -> List[Dict]:
        """Получаем 100 последних постов аккаунта
        """
        try:
            medias = self.instagram.get_medias(account, 100)
        except:
            medias = []
        result = []
        for media in medias:
            result.append({'id': media.identifier,
                'text': media.caption,
                'date': datetime.datetime.fromtimestamp(media.created_time),
                'likes': media.likes_count,
                'url': media.link
                })
        return result
    
    def get_comments_by_id(self, post_id: str) -> List[Dict]:
        """Получаем последние 10.000 комментариев к посту по ID
        """
        comments = self.instagram.get_media_comments_by_id(post_id, 10000)
        result = []
        if 'comments' in comments:
            for comment in comments['comments']:
                result.append({
                    'date': datetime.datetime.fromtimestamp(comment.created_at),
                    'text': comment.text,
                    '_is_fake': comment._is_fake,
                    'id': comment.identifier,
                    'from_username': comment.owner.username,
                    'from_full_name': comment.owner.full_name
                })
        return result
    
    def get_comments_by_code(self, code: str) -> List[Dict]:
        """Получаем последние 10.000 комментариев к посту по коду
        (Работает через раз)
        Args:
            code (str): Код поста

        Returns:
            List[Dict]: Список комментариев с мета-информацией
        """
        comments = self.instagram.get_media_comments_by_code(code, 10000)
        result = []
        if 'comments' in comments:
            for comment in comments['comments']:
                result.append({
                    'date': datetime.datetime.fromtimestamp(comment.created_at),
                    'text': comment.text,
                    '_is_fake': comment._is_fake,
                    'id': comment.identifier,
                    'from_username': comment.owner.username,
                    'from_full_name': comment.owner.full_name
                })
        return result
    
    def get_post_by_url(self, url: str) -> Dict:
        """Получаем пост по URL

        Args:
            url (str): Ссылка на пост

        Returns:
            Dict: Информация о посте
        """
        media = self.instagram.get_media_by_url(media_url=url)
        return {
            'id': media.identifier,
            'text': media.caption,
            'date': datetime.datetime.fromtimestamp(media.created_time),
            'likes': media.likes_count
        }

    def url2acc(self, url: str) -> str:
        """Извлекает из ссылки на аккаунт имя аккаунта

        Args:
            url (str): Ссылка на аккаунт. Например: https://www.instagram.com/new_ulyanovsk/

        Returns:
            str: Аккаунт для применения в методах парсинга: new_ulyanovsk
        """
        return url.split('https://www.instagram.com/')[1].split('/')[0]
    
    def url2code(self, url: str) -> str:
        """Получаем код поста из url

        Args:
            url (str): Ссылка на пост. Например: https://www.instagram.com/p/CHDn3eMMenH

        Returns:
            str: Код поста: CHDn3eMMenH
        """
        return url.split('https://www.instagram.com/p/')[1].split('/')[0]
    
    def get_post_likes(self, code: str) -> int:
        """Получаем количество лайков поста по его коду

        Args:
            code (str): Код поста

        Returns:
            int: Количество лайков
        """
        return self.instagram.get_media_likes_by_code(code)