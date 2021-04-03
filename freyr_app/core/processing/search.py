import os
from typing import List
import faiss
from sentence_transformers import SentenceTransformer, util
from django.conf import settings
from freyr_app import sentence_embedder


class FaissSearch:
    """Создание индекса с помощью faiss и sbert
    """
    def __init__(self):
        self.path = os.path.join(settings.TENSORS_PATH, 'articles.index.faiss')
        self.load()
        self.embedder = sentence_embedder
    
    def create_index(self, texts: List[str]) -> int:
        """Создание нового индекса

        Args:
            texts (List[str]): Список текстов для индекса

        Returns:
            int: количество материалов в индексе
        """
        embeddings = self.embedder.encode(texts)
        dimention = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimention)
        self.index.add(embeddings)
        return self.index.ntotal
    
    def add(self, texts: List[str]) -> tuple:
        """Добавление текстов в индекс.

        Args:
            texts (List[str]): Список текстов

        Returns:
            int: позиция первого материала этих добавляемых текстов в индексе
            int: Общее количество материалов в индексе
        """
        if self.index:
            start_idx = self.index.ntotal
            embeddings = self.embedder.encode(texts)
            self.index.add(embeddings)
            return start_idx, self.index.ntotal
        else:
            self.create_index(texts)
            return 0, self.index.ntotal
    
    def save(self):
        """Сохранение индекса на диск
        """
        if self.index:
            faiss.write_index(self.index, self.path)
    
    def load(self):
        """Загрузка индекса с диска
        """
        if os.path.isfile(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = None
    
    def search(self, query: str, top_n: int = 100) -> tuple:
        """Поиск по индексу

        Args:
            query (str): Поисковая фраза
            top_n (int, optional): Количество результатов

        Returns:
            tuple: Косинусы и индексы найденных материалов
        """
        if len(query) == 0:
            raise ValueError
        if not self.index:
            raise IndexError
        query = self.embedder.encode(query)
        D, I = self.index.search(query.reshape(1, query.shape[0]), k=top_n)
        return D, I
