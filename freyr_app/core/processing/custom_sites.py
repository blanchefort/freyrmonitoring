import logging
from django.conf import settings
from django.utils import timezone

from core.processing.predictor import DefineText
from core.processing.nlp import ner

from core.models import Site, Article, Entity, EntityLink
from core.crawlers import (
    get_newsroom24,
    get_vgoroden,
    get_newsnn,
    get_progorodnn,
    get_koza,
    get_pravdann
)

logger = logging.getLogger(__name__)

def save_articles(articles, site_url):
    """Сохраняем статьи ресурса
    """
    logger.info('Save article start')
    texts = [item['text'] for item in articles]
    logger.info(f'Count of texts: {len(texts)}')
    themes, sentiments = [], []
    dt = DefineText(texts=texts, model_path=settings.ML_MODELS)
    themes, _ = dt.article_theme()
    sentiments, _ = dt.article_sentiment()

    current_tz = timezone.get_current_timezone()

    for item, t, s in zip(articles, themes, sentiments):
        if Article.objects.filter(url=item['url']).count() == 0:
            article_id = Article.objects.create(
                url=item['url'],
                site=Site.objects.get(url=site_url),
                title=item['title'],
                text=item['text'],
                publish_date=current_tz.localize(item['date']),
                theme=t,
                sentiment=s
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
    logger.info('Saving articles complete!')

def scrape_custom_sites():
    """Обходим и сохраняем сайты с индивидуальными парсерами
    """
    logger.info('Start Custom Sites Scraping')

    #newsroom24
    site, _ = Site.objects.get_or_create(url='https://newsroom24.ru/archive/', title='newsroom24.ru', type='site')
    logger.info(site)
    result = get_newsroom24()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    #vgoroden
    site, _ = Site.objects.get_or_create(url='https://www.vgoroden.ru/', title='vgoroden.ru', type='site')
    logger.info(site)
    result = get_vgoroden()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    #get_newsnn
    site, _ = Site.objects.get_or_create(url='https://newsnn.ru/', title='newsnn.ru', type='site')
    logger.info(site)
    result = get_newsnn()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    #get_progorodnn
    site, _ = Site.objects.get_or_create(url='https://progorodnn.ru/news', title='progorodnn.ru', type='site')
    logger.info(site)
    result = get_progorodnn()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    #get_koza
    site, _ = Site.objects.get_or_create(url='https://koza.press/', title='koza.press', type='site')
    logger.info(site)
    result = get_koza()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    #get_pravdann
    site, _ = Site.objects.get_or_create(url='https://pravda-nn.ru/', title='pravda-nn.ru', type='site')
    logger.info(site)
    result = get_pravdann()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site.url)

    logger.info('Custom Sites Scraping complete!')