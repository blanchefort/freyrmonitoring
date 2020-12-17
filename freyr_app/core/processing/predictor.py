import torch
from transformers import BertTokenizer, BertForSequenceClassification

class DefineText:
    """Общий класс для определения различных типов текстов Бертами.
    На вход подаём массив сырых текстов:
    
    texts = [text_1, text_1, ..., text_N]
    
    Example:
    dt = DefineText(texts=texts, model_path='./models')
    themes, _ = dt.article_theme()
    """
    def __init__(self, texts, model_path):
        self.texts = texts
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        self.model_path = model_path
    
    def predictor(self, texts, tokenizer, model):
        """Общий метод, определяющий метки текстов
        """
        inputs = tokenizer(
            texts,
            padding='longest',
            truncation=True,
            max_length=512,
            return_tensors='pt')
        input_ids = inputs['input_ids'].to(self.device)
        token_type_ids = inputs['token_type_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        with torch.no_grad():
            logits = model(input_ids=input_ids, token_type_ids=token_type_ids, attention_mask=attention_mask)[0]
        probabilities = torch.softmax(logits, dim=1).to('cpu')
        labels = torch.argmax(probabilities, dim=1)
        return labels.tolist(), probabilities.tolist()
    
    def article_theme(self):
        """Метод определяет тему текста статьи.
        1 - статья подходит под региональные новости, обсуждающие власть
        0 - не подходит
        """
        tokenizer = BertTokenizer.from_pretrained('DeepPavlov/rubert-base-cased-sentence')
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
        tokenizer = BertTokenizer.from_pretrained('DeepPavlov/rubert-base-cased-sentence')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/article_sentiment')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)
    
    def comment_sentiment(self):
        """Метод определяет тональность комментария или произвольного (неновостного) поста
        1: 'Positive',
        0: 'Neutral',
        2: 'Negative',
        """
        tokenizer = BertTokenizer.from_pretrained('DeepPavlov/rubert-base-cased-sentence')
        model = BertForSequenceClassification.from_pretrained(f'{self.model_path}/article_sentiment')
        model.to(self.device)
        model.eval()
        
        return self.predictor(self.texts, tokenizer, model)