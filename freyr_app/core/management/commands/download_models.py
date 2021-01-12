"""Команда скачивания новых версий ML-моделей

$python manage.py download_models
"""
import warnings
warnings.filterwarnings("ignore")

import os, shutil
import wget
import logging
from transformers import BertTokenizer
from transformers import BertForSequenceClassification
from django.core.management.base import BaseCommand
from django.conf import settings

from core.models import categories, Category

logger = logging.getLogger(__name__)

freyr_files = [
    {'save_path': 'article_sentiment', 'file_name': 'config.json', 'url': 'https://www.dropbox.com/s/xppp7h47nvvpm5c/config.json?dl=1',},
    {'save_path': 'article_sentiment', 'file_name': 'pytorch_model.bin', 'url': 'https://www.dropbox.com/s/oqac1o1o9mcrslf/pytorch_model.bin?dl=1',},
    {'save_path': 'article_theme', 'file_name': 'config.json', 'url': 'https://www.dropbox.com/s/plsxvqk6aj052t1/config.json?dl=1',},
    {'save_path': 'article_theme', 'file_name': 'pytorch_model.bin', 'url': 'https://www.dropbox.com/s/3dwmakv1kql0gtn/pytorch_model.bin?dl=1',},
    {'save_path': 'gov_categories', 'file_name': 'classifier.pt', 'url': 'https://www.dropbox.com/s/knjbpwxj7vcizcf/classifier.pt?dl=1',},
    {'save_path': '', 'file_name': 'stopwords.txt', 'url': 'https://www.dropbox.com/s/regobpg4xciezt6/stopwords.txt?dl=1',},
    {'save_path': '', 'file_name': 'ru_bert_config.json', 'url': 'https://www.dropbox.com/s/02ih472utx9gcex/ru_bert_config.json?dl=1',},
]

class Command(BaseCommand):
    help = 'Команда скачивания новых версий ML-моделей'

    def handle(self, *args, **kwargs):
        # Создаём папки
        logger.info('Create Dirs')
        if os.path.isdir(settings.AUDIO_PATH):
            shutil.rmtree(settings.AUDIO_PATH, ignore_errors=True)
        os.makedirs(settings.AUDIO_PATH, exist_ok=True)
        if os.path.isdir(settings.ML_MODELS):
            shutil.rmtree(settings.ML_MODELS, ignore_errors=True)
        if not os.path.isdir(settings.CLUSTERS_PATH):
            os.makedirs(settings.CLUSTERS_PATH, exist_ok=True)

        # Качаем модели
        for ff in freyr_files:
            logger.info(f"Download model: {ff['save_path']}")
            save_path = os.path.join(settings.ML_MODELS, ff['save_path'])
            file_path = os.path.join(save_path, ff['file_name'])
            os.makedirs(save_path, exist_ok=True)
            if os.path.isfile(file_path):
                os.remove(file_path)
            wget.download(ff['url'], file_path)

        # Токенизаторы
        logger.info(f'Download tokenizers')
        # article_theme, article_sentiment
        BertTokenizer.from_pretrained(
            'DeepPavlov/rubert-base-cased-sentence').save_pretrained(
                os.path.join(settings.ML_MODELS, 'rubert-base-cased-sentence-tokenizer'))

        # gov_categories
        BertTokenizer.from_pretrained(
            'DeepPavlov/rubert-base-cased').save_pretrained(
                os.path.join(settings.ML_MODELS, 'rubert-base-cased-tokenizer'))
        
        # Модель и токенизатор анализа тональности статей и комментариев
        logger.info(f'Download Sentiment Models')
        for m_name in ('rubert-base-cased-sentiment', 'rubert-base-cased-sentiment-rusentiment'):
            BertForSequenceClassification.from_pretrained(
                f'blanchefort/{m_name}').save_pretrained(
                    os.path.join(settings.ML_MODELS, m_name))
            BertTokenizer.from_pretrained(
                f'blanchefort/{m_name}').save_pretrained(
                    os.path.join(settings.ML_MODELS, m_name))

        # Кальди
        logger.info(f'Download Kaldi')
        m_name = 'vosk-model-ru-0.10'
        wget.download(
            f'https://alphacephei.com/vosk/models/{m_name}.zip',
            os.path.join(settings.ML_MODELS, f'{m_name}.zip')
        )
        logger.info(f'Extracting Kaldi model files')
        shutil.unpack_archive(
            os.path.join(settings.ML_MODELS, f'{m_name}.zip')
        )
        
        if os.path.isdir(settings.KALDI):
            shutil.rmtree(settings.KALDI, ignore_errors=True)
        os.rename(m_name, settings.KALDI)
        os.remove(os.path.join(settings.ML_MODELS, f'{m_name}.zip'))

        # Устанавливаем названия категорий в БД
        if Category.objects.all().count() == 0:
            for cat in categories:
                Category.objects.create(name=cat)
