import logging

from ..models import Site
from ..crawlers import (
    NovgorodRuCrawler,
    VNRuCrawler
)
from .scrape_socio import save_articles

logger = logging.getLogger(__name__)


def scrape_custom_sites():
    """Обходим и сохраняем сайты с индивидуальными парсерами
    """
    logger.info('Start Custom Sites Scraping')

    # NovgorodRuCrawler
    crawler = NovgorodRuCrawler()
    logger.info(crawler.domain)
    site, _ = Site.objects.get_or_create(
        url='https://news.novgorod.ru/news/',
        title='«Новгород.ру»',
        type='site'
    )
    result = crawler.latest_posts()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site)
    
    # VNRuCrawler
    crawler = VNRuCrawler()
    logger.info(crawler.domain)
    site, _ = Site.objects.get_or_create(
        url='https://vnru.ru/news.html',
        title='«Великий Новгород.ру»',
        type='site'
    )
    result = crawler.latest_posts()
    logger.info(f'Found articles {len(result)}')
    if result is not None and len(result) > 0:
        save_articles(result, site)

    logger.info('Custom Sites Scraping complete!')