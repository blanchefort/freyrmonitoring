from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from django.conf import settings
import configparser
from typing import Dict, List

class TelegaParser:
    """Получаем информацию из Телеграма
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(settings.CONFIG_INI_PATH)
        self.api_id = config['TELEGA']['API_ID']
        self.api_hash = config['TELEGA']['API_HASH']
    
    async def channel_info(self, channel: str) -> Dict:
        """Информация о канале

        Args:
            channel (str): Логин аккаунта, либо ссылка на аккаунт

        Returns:
            Dict: Описание канала
        """
        try:
            async with TelegramClient('telega_session', self.api_id, self.api_hash) as client:
                await client.connect()
                channel = await client.get_entity(channel)
                return {
                    'id': channel.id,
                    'title': channel.title,
                }
        except UsernameNotOccupiedError:
            return {}
    
    async def last_messages(self, channel: str) -> List[Dict]:
        """Последние 1000 текстовых сообщений канала
        """
        result = []
        try:
            async with TelegramClient('telega_session', self.api_id, self.api_hash) as client:
                await client.connect()
                client(JoinChannelRequest(channel))
                channel_item = await client.get_entity(channel)
                async for message in client.iter_messages(channel_item, limit=100):
                    if len(message.message) > 1:
                        result.append({
                            # https://t.me/rt_russian/56086
                            'url': channel + '/' + str(message.id),
                            'date': message.date,
                            'text': message.text, # message.message
                            'views': message.views
                        })
            return result
        except:
            return {}
