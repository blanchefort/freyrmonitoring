import os
import re
from razdel import sentenize
from natasha import (Doc, 
                     NewsEmbedding, 
                     NewsNERTagger, 
                     Segmenter, 
                     MorphVocab, 
                     NewsMorphTagger)
import networkx as nx
from nltk.stem.snowball import SnowballStemmer

from django.conf import settings

emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)
segmenter = Segmenter()
morph_vocab = MorphVocab()
morph_tagger = NewsMorphTagger(emb)

stemmer = SnowballStemmer('russian')
G = nx.read_edgelist(path=os.path.join(settings.ML_MODELS, 'geograph.edgelist'), delimiter=':')

def lemmatize(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
    return [token.lemma for token in doc.tokens]

def ner(text: str) -> set:
    """Распознавание именованных сущностей
    """
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)
    doc.tag_morph(morph_tagger)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)

    for span in doc.spans:
        span.normalize(morph_vocab)
    ner_tokens = []
    for span in doc.spans:
        if len(span.normal) > 0:
            ner_tokens.append((span.normal, span.type))
        else:
            ner_tokens.append((span.text, span.type))
    return set(ner_tokens)

def get_title(text: str) -> str:
    """Генеарция заголовка

    Args:
        text ([str]): Текста поста

    Returns:
        [str]: Заголовок
    """
    text = text.replace('\n\r', ' ')
    text = text.replace('\n', ' ')
    sents = list(sentenize(text))
    if len(sents[0].text) > 0:
        title = sents[0].text
    elif len(sents) > 2:
        title = sents[1].text
    else:
        title = '(без заголовка)'
    title = title.replace('**', ' ')
    title = title.replace('__', ' ')
    return title.strip()

def deEmojify(text: str) -> str:
    """Удаляем эмоджи из текста
    https://stackoverflow.com/a/49986645

    Args:
        text (str): Текст

    Returns:
        str: Очищенный текст
    """
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    text = regrex_pattern.sub(r'', text)
    text = text.replace('**', ' ')
    text = text.replace('__', ' ')
    return text.strip()

def get_district(location: str) -> str:
    """Получаем муниципалитет, к которому относится локация

    Args:
        location (str): [description]

    Returns:
        str: [description]
    """
    location_variants = (
        location,
        stemmer.stem(location),
    )
    region = [n for n in G.neighbors('Россия')][0]
    for location in location_variants:
        if location in G:
            path = nx.dijkstra_path(G, location, region)
            if len(path) == 1:
                return 'region'
            return path[-2].split(',')[0]
    return False