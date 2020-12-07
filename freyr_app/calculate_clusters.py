'''Первоначальная разбивка на кластеры
'''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freyr_app.settings")
django.setup()

import torch
from processing.clustering import *
from core.models.article import Article
from core.models.entity import Entity, EntityLink
from django.conf import settings
from sentence_transformers import SentenceTransformer, util
from core.models.theme import Theme, ThemeArticles
import time
import datetime

def format_time(elapsed):
    elapsed_rounded = int(round((elapsed)))
    return str(datetime.timedelta(seconds=elapsed_rounded))
start_time = time.time()

articles = Article.objects.filter(theme=True).all()
print('articles len', len(articles))

lag_idx = []
lag_titles = []
lag_texts = []
for article in articles:
    lag_idx.append(article.id)
    lag_titles.append(article.title)
    lag_texts.append(article.text)

print('generate_corpus_embs')
corpus_embeddings = generate_corpus_embs(titles=lag_titles, texts=lag_texts)

print('generate_new_clusters')
(cluster_embeddings, 
 cluster_titles, 
 cluster_keywords, 
 cluster_articles) = generate_new_clusters(corpus_embeddings, lag_titles, lag_texts)

print('save clusters and links')
for cl_idx in range(0, len(cluster_embeddings)):
    theme_id = Theme.objects.create(
        name=cluster_titles[cl_idx],
        keywords=cluster_keywords[cl_idx]
    )
    torch.save(cluster_embeddings, os.path.join(settings.CLUSTERS_PATH, f'{theme_id}.pt'))
    theme = Theme.objects.get(theme_id)
    for art_id in get_system_ids(lag_idx=lag_idx, reltive_ids=cluster_articles[cl_idx]):
        ThemeArticles(
            theme_link=theme,
            article_link=Article.objects.get(art_id)
        ).save()

print('TOTAL TIME:', format_time(time.time()-start_time))
