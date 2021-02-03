import os
import logging
import torch
import datetime
import re
import RAKE
from sentence_transformers import SentenceTransformer, util

from django.conf import settings
from django.utils import timezone

from ..models import Article, Theme, ThemeArticles

logger = logging.getLogger(__name__)


class TextStreamClustering:
    """Методы кластеризации текстового потока
    """
    def __init__(self):
        self.Rake = RAKE.Rake(os.path.join(settings.ML_MODELS, 'stopwords.txt'))
        self.embedder = SentenceTransformer('distiluse-base-multilingual-cased')

    def generate_title(self, text):
        '''Создаём заголовок статьи из её главного ключевого слова
        Если текст настолько короткий, что не удалось извлечь ключевых слов,
        делаем заголовком весь текст
        '''
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'http\S+', '', text.strip(), flags=re.MULTILINE)
        keywords = self.Rake.run(text)
        if len(keywords) > 0:
            return keywords[0][0]
        return text

    def generate_kw(self, title, text, threshold):
        '''Преобразуем статью в строку из заголовка и ключевых слов
        '''
        kwd_text = title.replace('\xa0', ' ') + ', '
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'http\S+', '', text.strip(), flags=re.MULTILINE)
        keywords = self.Rake.run(text)
        for keyword, score in keywords:
            if score >= threshold:
                kwd_text += keyword + ', '
        if len(kwd_text) < 10:
            kwd_text = text
        return kwd_text

    def generate_corpus_embs(self, titles, texts):
        '''Генерируем эмбеддинги корпуса
        '''
        lag_kwds = []
        for title, text in zip(titles, texts):
            text = text.replace('\n', ' ')
            text = re.sub(r'http\S+', '', text.strip(), flags=re.MULTILINE)
            lag_kwds.append(self.generate_kw(title.replace('\xa0', ' '), text, 4.5))
        corpus_embeddings = self.embedder.encode(lag_kwds)
        return corpus_embeddings

    def article_similars(self, embeddings):
        '''Находим в корпусе все семантически похожие статьи
        '''
        similars = []
        for idx, query_embedding in enumerate(embeddings):
            print(len(query_embedding))
            cos_scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]
            cos_scores = cos_scores.cpu()
            sims = []
            for idx_sim, score in enumerate(cos_scores):
                if (score > .5) and (idx != idx_sim):
                    sims.append(idx_sim)
            similars.append(sims)
        return similars

    def select_maximal_cluster(self, items):
        '''находим самый большой кластер'''
        maximal = 0
        maximal_id = 0
        for idx in range(0, len(items)):
            if len(items[idx]) > maximal:
                maximal = len(items[idx])
                maximal_id = idx
        return maximal_id, [maximal_id]+items[maximal_id]

    def create_cluster(self, texts, titles):
        '''Создаём кластер из группы схожих материалов
        '''
        texts = [text.replace('\n', ' ').strip() for text in texts]
        texts = [re.sub(r'http\S+', '', text, flags=re.MULTILINE) for text in texts]
        titles = [title.replace('\xa0', ' ').strip() for title in titles]
        
        full_text = ''
        for text, title in zip(texts, titles):
            full_text += self.generate_kw(title, text, 6) + ' '
        cluster_embedding = self.embedder.encode(full_text, convert_to_tensor=True)
        
        item_kwds = []
        for text, title in zip(texts, titles):
            item_kwds.append(self.generate_kw(title, text, 4.5))
        item_embs = self.embedder.encode(item_kwds, convert_to_tensor=True)
        
        cos_scores = util.pytorch_cos_sim(cluster_embedding, item_embs)[0]
        max_score = cos_scores.max()
        for idx, score in enumerate(cos_scores):
            if score == max_score:
                return idx, cluster_embedding, item_kwds

    def select_cluster_articles(self, cluster_embedding, corpus_embeddings):
        '''Проходим по всему корпусу, и выбираем статьи, семантически похожие на кластер
        '''
        selected = []
        cos_scores = util.pytorch_cos_sim(cluster_embedding, corpus_embeddings)[0]
        cos_scores = cos_scores.cpu()
        max_score = cos_scores.max()
        for idx, score in enumerate(cos_scores):
            if score == max_score:
                max_id = idx
            if score > .5:
                selected.append(idx)
        return selected, max_id, max_score.item()

    def rearrange_list(self, lst, to_remove):
        '''Удаляем из списка индексы уже кластеризованных материалов
        '''
        new_lst = []
        for idx, content in enumerate(lst):
            if idx in to_remove:
                new_lst.append([])
            else:
                new_lst.append(content)
        return new_lst

    def get_system_ids(self, lag_idx, reltive_ids):
        '''Получаем системные идентификаторы статей
        '''
        system_ids = []
        for idx in reltive_ids:
            system_ids.append(lag_idx[idx])
        return system_ids

    def get_nonclustered_data(self, lag_idx, lag_titles, lag_texts, clustered_ids):
        '''Получаем корпус статей, которые не попали ни в один кластер
        '''
        new_lag_idx = []
        new_lag_titles = []
        new_lag_texts = []
        for idx in range(0, len(lag_idx)):
            if idx not in clustered_ids:
                new_lag_idx.append(lag_idx[idx])
                new_lag_titles.append(lag_titles[idx])
                new_lag_texts.append(lag_texts[idx])
        return new_lag_idx, new_lag_titles, new_lag_texts

    def generate_new_clusters(self, corpus_embeddings, lag_titles, lag_texts):
        '''Выявляем кластеры, пока есть статьи-кандидаты
        '''
        similars = self.article_similars(embeddings=corpus_embeddings)
        candidates = 0
        for item in similars:
            if len(item) > 0:
                candidates += 1
        cluster_embeddings = []
        cluster_titles = []
        cluster_keywords = []
        cluster_articles = []
        while candidates > 0:
            # находим самый большой кластер
            idx, items_ids = self.select_maximal_cluster(similars)
            # берём все заголовки и тексты этих схожих материалов
            items_titles = [lag_titles[i] for i in items_ids]
            items_texts = [lag_texts[i] for i in items_ids]
            # преобразуем схожие материалы в новый кластер
            top_idx, cluster_embedding, cluster_kwds = self.create_cluster(items_texts, items_titles)
            if len(items_titles[top_idx]) < 1:
                cluster_title = self.generate_title(items_texts[top_idx])
            else:
                cluster_title = items_titles[top_idx]

            # Проходим по всему корпусу, и выбираем статьи, семантически похожие на кластер
            selected, max_id, max_score = self.select_cluster_articles(cluster_embedding, corpus_embeddings)
            if (top_idx != max_id) and max_score > .7:
                if len(lag_titles[max_id]) < 1:
                    cluster_title = self.generate_title(lag_titles[max_id])
                else:
                    cluster_title = lag_titles[max_id]

            # сохраняем новый кластер
            cluster_embeddings.append(cluster_embedding)
            cluster_titles.append(cluster_title)
            cluster_keywords.append(cluster_kwds)
            cluster_articles.append(selected)

            # Удаляем индексы уже кластеризованных материалов
            similars = self.rearrange_list(similars, selected)
            # пересчитываем оставшихся кандидатов
            candidates = 0
            for item in similars:
                if len(item) > 0:
                    candidates += 1
        return cluster_embeddings, cluster_titles, cluster_keywords, cluster_articles


def clustering(delta_hours=5):
    """Кластеризуем материалы
    
    delta_hours - за сколько предыдущих часов брать статьи из БД для кластеризации.
    """
    logger.info('Start Clustering')
    start_date = timezone.now()
    end_date = timezone.now() - datetime.timedelta(hours=5*24)
    themes = Theme.objects.filter(
        theme_articles__article_link__publish_date__range=[end_date, start_date])
    tsc = TextStreamClustering()
    if len(themes) == 0:
        logger.info('New Clustering')
        articles = Article.objects.filter(theme=True).all()

        lag_idx = [article.id for article in articles]
        lag_titles = [article.title for article in articles]
        lag_texts = [article.text for article in articles]
        
        logger.info('generate_corpus_embs')
        corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)

        logger.info('generate_new_clusters')
        (cluster_embeddings, 
        cluster_titles, 
        cluster_keywords, 
        cluster_articles) = tsc.generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)

        logger.info('save clusters and links')
        for cl_idx in range(0, len(cluster_embeddings)):
            theme = Theme.objects.create(
                name=cluster_titles[cl_idx],
                keywords=cluster_keywords[cl_idx]
            )
            torch.save(cluster_embeddings[cl_idx], os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
            for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
                ThemeArticles(
                    theme_link=theme,
                    article_link=Article.objects.get(pk=art_id)
                ).save()
    else:
        logger.info('TimeSiquenceClustering')
        delta_hours = -delta_hours
        start_date = timezone.now()
        end_date = timezone.now() + datetime.timedelta(hours=delta_hours)
        articles = Article.objects.filter(theme=True).filter(
                    publish_date__gte=end_date,
                    publish_date__lte=start_date
                )
        logger.info(f'Len of articles len(articles)')
        lag_idx = [article.id for article in articles]
        lag_titles = [article.title for article in articles]
        lag_texts = [article.text for article in articles]
        logger.info('='*10)
        logger.info('CHECK LENGTHS OF CONTENT')
        logger.info('Titles:')
        for i in lag_titles:
            logger.info(len(i))
        logger.info('Texts:')
        for i in lag_texts:
            logger.info(len(i))
        # Получаем эмбеддинги новой выборки
        logger.info('Получаем эмбеддинги новой выборки')
        corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)
        logger.info('Corpus embeddings:')
        for i in corpus_embeddings:
            logger.info(len(i))
        logger.info('='*10)
        # Прогоняем статьи по имеющимся кластерам
        logger.info('Прогоняем статьи по имеющимся кластерам')
        selected_articles = []
        #TODO: Темы надо тоже по времени ограничивать
        for theme in themes:
            cluster_new_articles = []
            cluster_embedding = torch.load(os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
            logger.info(f'Cluster embedding, {cluster_embedding.shape}')
            selected, _, _ = tsc.select_cluster_articles(cluster_embedding, corpus_embeddings)
            if len(selected) > 0:
                cluster_new_articles = selected
                selected_articles += selected
            # Идентификаторы статей кластера для сохранения в БД
            for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_new_articles):
                ThemeArticles.objects.get_or_create(
                    theme_link=theme,
                    article_link=Article.objects.get(pk=art_id)
                )
        # Смотрим, остались ли ещё неразмеченные статьи
        logger.info('Смотрим, остались ли ещё неразмеченные статьи')
        if len(set(selected_articles)) < len(lag_idx):
            lag_idx, lag_titles, lag_texts = tsc.get_nonclustered_data(
                lag_idx=lag_idx,
                lag_titles=lag_titles,
                lag_texts=lag_texts,
                clustered_ids=set(selected_articles))
            corpus_embeddings = tsc.generate_corpus_embs(titles=lag_titles, texts=lag_texts)

            # Новые кластеры
            logger.info('Новые кластеры')
            (cluster_embeddings, 
            cluster_titles, 
            cluster_keywords, 
            cluster_articles) = tsc.generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)

            # Сохраняем новые кластеры
            logger.info('Сохраняем новые кластеры')
            for cl_idx in range(0, len(cluster_embeddings)):
                theme = Theme.objects.create(
                    name=cluster_titles[cl_idx],
                    keywords=cluster_keywords[cl_idx]
                )
                torch.save(cluster_embeddings[cl_idx], os.path.join(settings.CLUSTERS_PATH, f'{theme.id}.bin'))
                for art_id in tsc.get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
                    ThemeArticles.objects.get_or_create(
                        theme_link=theme,
                        article_link=Article.objects.get(pk=art_id)
                    )
    logger.info('End Clustering')