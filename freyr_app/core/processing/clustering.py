import os
import logging
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
import torch
from ..models import Article, Theme, ThemeArticles
from freyr_app import sentence_embedder

logger = logging.getLogger(__name__)


def community_detection(embeddings, threshold=0.75, min_community_size=10, init_max_size=1000):
    """
    https://github.com/UKPLab/sentence-transformers/blob/master/examples/applications/clustering/fast_clustering.py
    Function for Fast Community Detection
    Finds in the embeddings all communities, i.e. embeddings that are close (closer than threshold).
    Returns only communities that are larger than min_community_size. The communities are returned
    in decreasing order. The first element in each list is the central point in the community.
    """

    # Compute cosine similarity scores
    cos_scores = util.pytorch_cos_sim(embeddings, embeddings)

    # Minimum size for a community
    top_k_values, _ = cos_scores.topk(k=min_community_size, largest=True)

    # Filter for rows >= min_threshold
    extracted_communities = []
    for i in range(len(top_k_values)):
        if top_k_values[i][-1] >= threshold:
            new_cluster = []

            # Only check top k most similar entries
            top_val_large, top_idx_large = cos_scores[i].topk(k=init_max_size, largest=True)
            top_idx_large = top_idx_large.tolist()
            top_val_large = top_val_large.tolist()

            if top_val_large[-1] < threshold:
                for idx, val in zip(top_idx_large, top_val_large):
                    if val < threshold:
                        break

                    new_cluster.append(idx)
            else:
                # Iterate over all entries (slow)
                for idx, val in enumerate(cos_scores[i].tolist()):
                    if val >= threshold:
                        new_cluster.append(idx)

            extracted_communities.append(new_cluster)

    # Largest cluster first
    extracted_communities = sorted(extracted_communities, key=lambda x: len(x), reverse=True)

    # Step 2) Remove overlapping communities
    unique_communities = []
    extracted_ids = set()

    for community in extracted_communities:
        add_cluster = True
        for idx in community:
            if idx in extracted_ids:
                add_cluster = False
                break

        if add_cluster:
            unique_communities.append(community)
            for idx in community:
                extracted_ids.add(idx)

    return unique_communities


class TextStreamClustering:
    """Методы кластеризации текстового потока
    """
    def __init__(self):
        self.embedder = sentence_embedder
    
    def clustering(self, texts: List[str], titles: List[str]) -> List[List[int]]:
        """Кластеризация текстов

        Args:
            texts (List[str]): Список текстов
            titles (List[str]): Список заголовков

        Returns:
            List[List[int]]: Список кластеров со списком id текстов в каждом кластере. 
            Первым в списке идёт id текста, являющегося центром кластера
        """
        embeddings = self.embedder.encode([t1 + '[SEP]' + t2 for t1, t2 in zip(titles, texts)])
        clusters = community_detection(embeddings, min_community_size=4, threshold=0.6, init_max_size=len(embeddings))
        return clusters

    def continuous_clustering(
        self, 
        texts: List[str], 
        titles: List[str], 
        clust_texts: List[str], 
        clust_titles: List[str]) -> tuple:
        """Кластеризация с учётом уже существующих кластеров

        Args:
            texts: (List[str]): список текстов для кластеризации
            titles: (List[str]): список заголовков для кластеризации
            clust_texts: (List[str]): список центральных текстов существующих кластеров
            clust_titles: (List[str]): список центральных заголовков существующих кластеров
        
        Возвращает кореж из 2-х элементов:
            словарь - дополнение статей для существующих кластеров.
                Вид: {cluster_idx: [article_idx, article_idx]}
            Список кластеров со списком id текстов в каждом кластере. 
            Первым в списке идёт id текста, являющегося центром кластера
        """
        cluster_embeddings = self.embedder.encode([t1 + ' [SEP] ' + t2 for t1, t2 in zip(clust_titles, clust_texts)])
        embeddings = self.embedder.encode([t1 + ' [SEP] ' + t2 for t1, t2 in zip(titles, texts)])
        cosine_scores = util.pytorch_cos_sim(embeddings, cluster_embeddings)
        addenta_to_clusters = {}
        for i in range(len(texts)):
            for j in range(len(clust_texts)):
                if cosine_scores[i][j] > .6:
                    if j in addenta_to_clusters.keys():
                        addenta_to_clusters[j].append(i)
                    else:
                        addenta_to_clusters[j] = [i]
        
        # Удаляем занятые статьи. И, если статьи ещё остались, проводим новую кластеризацию по ним
        reselved_articles = set()
        for c in addenta_to_clusters.keys():
            reselved_articles.update(addenta_to_clusters[c])
        text_ids = [i for i in range(len(texts))]
        for i in reselved_articles:
            text_ids.remove(i)
        
        if len(text_ids) > 5:
            new_texts = [texts[i] for i in text_ids]
            new_titles = [titles[i] for i in text_ids]
            clusters = self.clustering(new_texts, new_titles)
            new_clusters = []
            for cluster in clusters:
                new_cluster = []
                for i in cluster:
                    selected_text = new_texts[i]
                    selected_index = texts.index(selected_text)
                    new_cluster.append(selected_index)
                new_clusters.append(new_cluster)
        
        return addenta_to_clusters, new_clusters

    def closest_title(self, cluster_core: str, cluster_titles: List[str]) -> str:
        """Выбираем наиболее близкий по косинусу заголовок к центру кластера

        Args:
            cluster_core (str): Текст центра кластера
            cluster_titles (List[str]): Все заголовки кластера

        Returns:
            str: Ближайший кластер
        """
        titles_embedding = self.embedder.encode(cluster_titles)
        core_embedding = self.embedder.encode(cluster_core)
        cosine_scores = util.pytorch_cos_sim(titles_embedding, core_embedding)
        best_title_idx = torch.argmax(cosine_scores[0]).item()
        return cluster_titles[best_title_idx]

    