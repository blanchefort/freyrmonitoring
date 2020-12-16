from django.test import TestCase
import validators
import datetime
from core.crawlers import (
    get_koza,
    get_newsnn,
    get_newsroom24,
    get_pravdann,
    get_progorodnn,
    get_vgoroden
)

# Стандартные парсеры: соцсети

# Кастомные парсеры для Заказчика
class KozaTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_koza()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

class NewsnnTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_newsnn()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

class Newsroom24TestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_newsroom24()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

class PravdannTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_pravdann()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

class ProgorodnnTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_progorodnn()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

class VgorodenTestClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.response = get_vgoroden()

    def test_response(self):
        self.assertTrue(len(self.response)>0)
    
    def test_url(self):
        result = [validators.url(item['url']) for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_title(self):
        result = [len(item['title'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_text(self):
        result = [len(item['text'])>0 for item in self.response]
        self.assertEquals(result, len(self.response)*[True])

    def test_date(self):
        result = [type(item['date']) == datetime.datetime for item in self.response]
        self.assertEquals(result, len(self.response)*[True])