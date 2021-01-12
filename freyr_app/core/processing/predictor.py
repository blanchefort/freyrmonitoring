import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from django.conf import settings
from core.models import categories
from core.nn import CategoryClassifier

class DefineText:
    """Общий класс для определения различных типов текстов Бертами.
    На вход подаём массив сырых текстов:
    
    texts = [text_1, text_1, ..., text_N]
    
    Example:
    dt = DefineText(texts=texts, model_path='./models')
    themes, _ = dt.article_theme()
    """
    def __init__(self, texts):
        self.texts = []
        for text in texts:
            if len(text) == 0:
                self.texts.append('(без текста)')
            else:
                self.texts.append(text)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        self.model_path = settings.ML_MODELS
    
    @torch.no_grad()
    def predictor(self, texts, tokenizer, model):
        """Общий метод, определяющий метки текстов
        """
        result_labels, result_probs = [], []
        for batch in range(0, len(texts), settings.BATCH_SIZE):
            inputs = tokenizer(
                texts[batch:batch+settings.BATCH_SIZE],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt')
            logits = model(**inputs.to(self.device))[0]
            probabilities = torch.softmax(logits, dim=1).to('cpu')
            labels = torch.argmax(probabilities, dim=1)
            result_labels.extend(labels.tolist())
            result_probs.extend(probabilities.tolist())
        return result_labels, result_probs
    
    @torch.no_grad()
    def multilabel_predictor(self, texts, tokenizer, model):
        """Метод для определения нескольких меток для текста
        (Для кастомных моделей, не из коробки Трансформера).
        """
        result_labels, result_probs = [], []
        for batch in range(0, len(texts), settings.BATCH_SIZE):
            inputs = tokenizer(
                texts[batch:batch+settings.BATCH_SIZE],
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors='pt')
            input_ids = inputs['input_ids'].to(self.device)
            attention_mask = inputs['attention_mask'].to(self.device)
            logits = model(input_ids, attention_mask)
            predicted = torch.sigmoid(logits) > 0.415
            predicted = predicted.cpu().tolist()
            for item in predicted:
                item_result = []
                result_probs.append(item)
                for cat_idx, cat_label in enumerate(item):
                    if cat_label == True:
                        item_result.append(categories[cat_idx])
                        if categories[cat_idx] == 'Без темы':
                            break
                result_labels.append(item_result)
        return result_labels, result_probs
    
    def article_theme(self):
        """Метод определяет тему текста статьи.
        1 - статья подходит под региональные новости, обсуждающие власть
        0 - не подходит
        """
        tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/rubert-base-cased-sentence-tokenizer')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/article_theme')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)
    
    def article_sentiment(self):
        """Метод определяет тональность новостной статьи
        1: 'Positive',
        0: 'Neutral',
        2: 'Negative',
        """
        tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/rubert-base-cased-sentence-tokenizer')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/article_sentiment')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)
    
    def happiness_category(self):
        """Определение категорий статей и постов
        """
        tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/rubert-base-cased-tokenizer')
        model = CategoryClassifier()
        model.load_state_dict(torch.load(os.path.join(self.model_path, 'gov_categories', 'classifier.pt')), strict=False)
        model.to(self.device)
        model.eval()
        return self.multilabel_predictor(self.texts, tokenizer, model)
    
    def happiness_sentiment(self):
        """Определение тональности статьи для расчёта индекса счастья
        """
        tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/rubert-base-cased-sentiment')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/rubert-base-cased-sentiment')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)
    
    def comment_sentiment(self):
        """Метод определяет тональность комментария
        1: 'Positive',
        0: 'Neutral',
        2: 'Negative',
        """
        tokenizer = BertTokenizer.from_pretrained(f'{self.model_path}/rubert-base-cased-sentiment-rusentiment')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/rubert-base-cased-sentiment-rusentiment')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)