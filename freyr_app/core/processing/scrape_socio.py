import logging
import configparser
import datetime

from django.conf import settings
from django.utils import timezone

from core.processing.predictor import DefineText
from core.processing.nlp import ner

from core.models import Site, Article, Entity, EntityLink, Comment
from core.crawlers import VKParser, InstaParser, OKParser, TwitterParser, YTParser

logger = logging.getLogger(__name__)
vk = VKParser()
insta = InstaParser(set_proxy=False)
ok = OKParser()
twi = TwitterParser()

config = configparser.ConfigParser()
config.read(settings.CONFIG_INI_PATH)
yt = YTParser(
    api=config['YOUTUBE']['KEY'],
    audio_path=settings.AUDIO_PATH,
    kaldi_path=settings.KALDI
    )

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
    texts = [item['text'] for item in articles if len(item['text']) > 0]
    logger.info(f'Count of texts: {len(texts)}')
    themes, sentiments = [], []
    if len(texts) > 0:
        dt = DefineText(texts=texts, model_path=settings.ML_MODELS)
        themes, _ = dt.article_theme()
        sentiments, _ = dt.article_sentiment()

        current_tz = timezone.get_current_timezone()

        for item, t, s in zip(articles, themes, sentiments):
            if Article.objects.filter(url=item['url']).count() == 0:
                try:
                    date = current_tz.localize(item['date'])
                except:
                    date = item['date']
                article_id = Article.objects.create(
                    url=item['url'],
                    site=site,
                    title=item.get('title', '(без заголовка)'),
                    text=item.get('text', '(без текста)'),
                    publish_date=date,
                    theme=t,
                    sentiment=s,
                    likes=item.get('likes', 0),
                )
                # Сущности
                if t == 1:
                    entities = ner(item['text'])
                    for entity in entities:
                        obj, created = Entity.objects.get_or_create(name=entity[0], type=entity[1])
                        EntityLink.objects.create(
                            entity_link=obj,
                            article_link=article_id
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
    # TODO: Изменить дату публикации 
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
                        if len(text) > 0 and len(description) > 0:
                            dt = DefineText(texts=[text], model_path=settings.ML_MODELS)
                            theme, _ = dt.article_theme()
                            sentiment, _ = dt.article_sentiment()
                            Article.objects.create(
                                url=description['webpage_url'],
                                site=site,
                                title=description['title'],
                                text=text,
                                publish_date=timezone.now(),
                                theme=theme[0],
                                sentiment=sentiment[0],
                                likes=description['like_count'],
                            )
            except:
                logger.warning(f'Cant catch data from {site.url}')
    logger.info('Stop socio posts collecting')

def collect_commets():
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