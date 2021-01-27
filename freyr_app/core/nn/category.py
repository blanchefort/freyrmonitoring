"""Определяет категории текстов
"""
import os
import torch
import torch.nn as nn
from transformers import BertConfig, BertModel

from django.conf import settings


class CategoryClassifier(nn.Module):
    def __init__(self):
        super(CategoryClassifier, self).__init__()
        config = BertConfig.from_pretrained(os.path.join(settings.ML_MODELS, 'ru_bert_config.json'))
        self.bert = BertModel(config)
        self.classifier = nn.Sequential(
            nn.BatchNorm1d(768),
            nn.Dropout(p=0.6),
            nn.ReLU(),
            nn.Linear(768, 18),
        )
    
    def mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        out = self.mean_pooling(out, attention_mask)
        out = self.classifier(out)
        return out
