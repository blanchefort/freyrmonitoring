from typing import List, Dict
from django.conf import settings
import configparser
import tweepy

class TwitterParser:
    """Получаем информацию из Твиттера
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(settings.CONFIG_INI_PATH)
        auth = tweepy.OAuthHandler(
            consumer_key=config['TWITTER']['CONSUMER_KEY'],
            consumer_secret=config['TWITTER']['CONSUMER_SECRET'])
        self.api = tweepy.API(auth)
    
    def get_user(self, name: str) -> Dict:
        """Получаем информацию о пользователе
        """
        user = self.api.get_user(name)
        return {
            'name': user.name,
            'location': user.location,
            'friends_count': user.friends_count,
            'followers_count': user.followers_count
        }
    
    def get_posts(self, name: str) -> List:
        """Получаем 100 последних статусов пользователя
        """
        response = self.api.user_timeline(name, count=100, tweet_mode='extended')
        result = []
        for status in response:
            result.append({
                'id': status.id,
                'date': status.created_at,
                'retweet_count': status.retweet_count,
                'favorite_count': status.favorite_count,
                'text': status.full_text
            })
        return result