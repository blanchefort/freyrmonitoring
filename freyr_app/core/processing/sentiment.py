import os
from typing import List
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from django.conf import settings
from ..models import categories
from ..nn import CategoryClassifier
from .nlp import preprocess_text


class Sentimenter:
    """Класс для быстрого определния сентимента батча текстов
    """
    def __init__(self, model_type='rubert-base-cased-sentiment'):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        self.model_path = settings.ML_MODELS
        self.tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/{model_type}')
        self.model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/{model_type}')
        self.model.to(self.device)
        self.model.eval()
    

    @torch.no_grad()
    def __call__(self, texts: List[str]) -> List[int]:
        texts = list(map(preprocess_text, texts))
        result_labels = []
        for batch in range(0, len(texts), settings.BATCH_SIZE):
            inputs = self.tokenizer(
                texts[batch:batch+settings.BATCH_SIZE],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt')
            logits = self.model(**inputs.to(self.device))[0]
            probabilities = torch.softmax(logits, dim=1).to('cpu')
            labels = torch.argmax(probabilities, dim=1)
            result_labels.extend(labels.tolist())
        return result_labels
