import logging
import configparser
import datetime

from django.conf import settings
from django.utils import timezone

from core.models import Site, Article, Comment
from core.crawlers import (
    VKParser,
    InstaParser,
    OKParser,
    TwitterParser,
    YTParser,
    TelegaParser)

logger = logging.getLogger(__name__)
vk = VKParser()
insta = InstaParser(set_proxy=False)
ok = OKParser()
twi = TwitterParser()
telega = TelegaParser()

config = configparser.ConfigParser()
config.read(settings.CONFIG_INI_PATH)
yt = YTParser(
    api=config['YOUTUBE']['KEY'],
    audio_path=settings.AUDIO_PATH,
    kaldi_path=settings.KALDI
    )

def create_datetime(value):
    if isinstance(value, datetime.datetime) and timezone.is_aware(value):
        return value
    else:
        current_tz = timezone.get_current_timezone()
        return current_tz.localize(value)

def views_as_number(views):
    if type(views) == int:
        return views
    if type(views) == float:
        return int(views)
    if views is None:
        return 0
    if 'K' in views:
        views = views.replace('K', '')
        views = float(views) * 1_000
    elif 'M' in views:
        views = views.replace('M', '')
        views = float(views) * 1_000_000
    return int(float(views))

def save_comments(comments, post):
    """Сохраняем комментарии определённого поста

    Args:
        comments (List[Dict]): Список собранных комментариев
        post ([core.models.Article]): Объект, которому принадлежат комментарии
    """
    for comment in comments:
        # TODO: Нужно выработать принципы идентификации комментариев
        Comment.objects.update_or_create(
            article=post,
            system_id=comment.get('system_id', None),
            text=comment.get('text', '---'),
            publish_date=comment.get('date', ''),
            sentiment=3,
            likes=comment.get('likes', 0),
            dislikes=comment.get('dislikes', 0),
            username=comment.get('username', None),
            userid=comment.get('userid', None),
        )

def save_articles(articles, site):
    """Сохраняем статьи ресурса
    """
    logger.info('Save posts start')
    if len(articles) > 0:
        for item in articles:
            if Article.objects.filter(url=item['url']).count() == 0:
                date = create_datetime(item['date'])
                Article.objects.create(
                    url=item['url'],
                    site=site,
                    title=item.get('title', '(без заголовка)'),
                    text=item.get('text', '(без текста)'),
                    publish_date=date,
                    theme=False,
                    sentiment=9,
                    likes=views_as_number(item.get('likes', 0)),
                    dislikes=views_as_number(item.get('dislikes', 0)),
                    views=views_as_number(item.get('views', 0)),
                )
            else:
                article = Article.objects.filter(url=item['url'])
                article.update(
                    likes=views_as_number(item.get('likes', 0)),
                    dislikes=views_as_number(item.get('dislikes', 0)),
                    views=views_as_number(item.get('views', 0)),
                )
    logger.info('Saving posts complete!')

def collect_socio_posts():
    """Собираем посты из соцсетей
    """
    logger.info('Start socio posts collecting')
    # ВК домены
    sites = Site.objects.filter(type='vk_domain')
    if len(sites) > 0:
        logger.info('Start vk_domain')
        for site in sites:
            result = []
            try:
                domain, _ = vk.url2domain(site.url)
                result = vk.latest_posts(domain)
            except:
                logger.warning(f'Cant catch data from {site.url}')
            if len(result) > 0:
                save_articles(result, site)

    # ВК ИДишники
    sites = Site.objects.filter(type='vk_owner')
    if len(sites) > 0:
        logger.info('Start vk_owner')
        for site in sites:
            result = []
            try:
                domain, _ = vk.url2domain(site.url)
                result = vk.latest_posts(domain)
            except:
                logger.warning(f'Cant catch data from {site.url}')
            if len(result) > 0:
                save_articles(result, site)

    # Инста
    sites = Site.objects.filter(type='insta')
    if len(sites) > 0:
        logger.info('Start insta')
        for site in sites:
            result = []
            try:
                account = insta.url2acc(site.url)
                result = insta.get_last_posts(account)
            except:
                logger.warning(f'Cant catch data from {site.url}')
            if len(result) > 0:
                save_articles(result, site)

    # Одноклассники домен
    sites = Site.objects.filter(type='odnoklassniki_domain')
    if len(sites) > 0:
        logger.info('Start odnoklassniki_domain')
        for site in sites:
            ok_post_links = []
            try:
                ok_post_links = ok.get_latest_posts(site.url)
            except:
                logger.warning(f'Cant catch data from {site.url}')
            if len(ok_post_links) > 0:
                result = []
                for link in ok_post_links:
                    try:
                        post_data, _ = ok.get_post(link)
                        result.append(post_data)
                    except:
                        logger.warning(f'Cant catch data from {link}')
                if len(result) > 0:
                    save_articles(result, site)

    # Ютуб
    sites = Site.objects.filter(type='youtube')
    if len(sites) > 0:
        logger.info('Start youtube')
        for site in sites:
            result = []
            try:
                latest_links = yt.get_latest_videos_by_channel_link(url=site.url)
                for link in latest_links:
                    if Article.objects.filter(url=link['url']).count() == 0:
                        text, description = yt.video2data(link['url'])
                        result.append({
                            'url': link['url'],
                            'title': description['title'],
                            'text': text,
                            'date': description['upload_date'],
                            'likes': description['like_count'],
                            'dislikes': description['dislike_count'],
                            'views': description['view_count'],
                        })
            except:
                logger.warning(f'Cant catch data from {site.url}')
            
            if len(result) > 0:
                    save_articles(result, site)

    logger.info('Stop socio posts collecting')

def collect_comments():
    """Собираем комментарии к сохранённым постам.
    Временной лаг - неделя
    """
    logger.info('Start comment collecting')
    delta_hours = -1 * 24 * 7
    start_date = timezone.now()
    end_date = timezone.now() + datetime.timedelta(hours=delta_hours)
    # ВК domain
    # .filter(theme=True) Нельзя ставить, т.к. нам нужны все посты для благополучия
    posts = Article.objects.filter(site__type='vk_domain').filter(
        publish_date__gte=end_date,
        publish_date__lte=start_date
        )
    if len(posts) > 0:
        logger.info('Start VK domain comment collecting')
        for post in posts:
            comments = []
            try:
                owner_id, post_id = vk.url2post(post.url)
                comments = vk.post_comments(owner_id, post_id)
            except:
                logger.warning(f'Cant get comments for {post.url}')
            if len(comments) > 0:
                save_comments(comments, post)
    

    # ВК vk_owner
    posts = Article.objects.filter(site__type='vk_owner').filter(
        publish_date__gte=end_date,
        publish_date__lte=start_date
        )
    if len(posts) > 0:
        logger.info('Start VK vk_owner comment collecting')
        for post in posts:
            comments = []
            try:
                owner_id, post_id = vk.url2post(post.url)
                comments = vk.post_comments(owner_id, post_id)
            except:
                logger.warning(f'Cant get comments for {post.url}')
            if len(comments) > 0:
                save_comments(comments, post)
    
    # Insta
    posts = Article.objects.filter(site__type='insta').filter(
        publish_date__gte=end_date,
        publish_date__lte=start_date
        )
    if len(posts) > 0:
        logger.info('Start insta comment collecting')
        for post in posts:
            comments = []
            try:
                media_code = insta.url2code(post.url)
                comments = insta.get_comments_by_code(media_code)
            except:
                logger.warning(f'Cant get comments for {post.url}')
            if len(comments) > 0:
                save_comments(comments, post)

async def collect_telega_posts():
    """Собираем последние сообщения из Телеграма
    """
    logger.info('START TELEGRAM POSTS COLECCTION')
    channels = Site.objects.filter(type='telega')
    for channel in channels:
        logger.info(f'CHANNEL: {channel}')
        results = []
        try:
            results = await telega.last_messages(channel.url)
        except:
            logger.error(f'CANT GET DATA FOR TG-CHANNEL {channel}')
        
        if len(results) > 0:
            save_articles(results, channel)
    
    logger.info('TELEGRAM POSTS COLECCTION COMPLETE')