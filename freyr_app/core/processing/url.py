from typing import Tuple
from purl import URL

def process_url(link: str) -> Tuple:
    """Выводим мета-информацию о ссылке

    Args:
        link (str): Ссылка

    Returns:
        Tuple: Мета-информация:
            - Тип домена
            - Ссылка для сохранения в БД
    """
    url = URL.from_string(link)
    if 'vk.com' in url.host():
        if 'public' in url.path_segment(0):
            # id = url.path_segment(0).split('public')[1]
            # id = -1 * int(id)
            type = 'vk_owner'
        elif 'club' in url.path_segment(0):
            # id = url.path_segment(0).split('club')[1]
            # id = -1 * int(id)
            type = 'vk_owner'
        else:
            type = 'vk_domain'
            # id = url.path_segment(0)
        return type, link
    elif 'ok.ru' in url.host():
        return 'odnoklassniki_domain', link
    elif 'twitter.com' in url.host():
        return 'twi', link
    elif 'instagram.com' in url.host():
        return 'insta', link
    elif 'youtube.com' in url.host():
        return 'youtube', link
    elif 'facebook.com' in url.host():
        return 'facebook', link
    else:
        return 'site', url.scheme() + '://' + url.host()