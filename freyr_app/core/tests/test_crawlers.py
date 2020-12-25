from django.test import TestCase
import validators
import datetime
from core.crawlers import (
    NovgorodRuCrawler,
    VNRuCrawler
)

# Стандартные парсеры: соцсети

class NovgorodRuTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crawler = NovgorodRuCrawler()
    
    def test_posts(self):
        response = self.crawler.latest_posts()
        self.assertTrue(len(response)>0)
    
    def test_comments(self):
        link = 'https://news.novgorod.ru/news/nerabotayushchikh-pensionerov-zhdt-indeksaciya-pensiy--176964.html'
        response = self.crawler.latest_comments(link)
        self.assertTrue(len(response)>0)

# class VNRuTestClass(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.crawler = VNRuCrawler()
    
#     def test_posts(self):
#         response = self.crawler.latest_posts()
#         self.assertTrue(len(response)>0)
    
#     async def test_comments(self):
#         link = 'https://vnru.ru/news/52954-salamandra-zhivushchaya-v-veryazhskom-parke-uteplilas.html'
#         response = await self.crawler.latest_comments(link)
#         self.assertTrue(len(response)>0)