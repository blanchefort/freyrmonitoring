import os
import re
from typing import List
from dataclasses import dataclass
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
from .named_entity import NamedEntity
import warnings


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
    warnings.warn('К удалению. Заменится на `extract_entities`', DeprecationWarning)
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


def extract_entities(text: str) -> List[NamedEntity]:
    """Распознавание именованных сущностей"""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)
    doc.tag_morph(morph_tagger)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)

    for span in doc.spans:
        span.normalize(morph_vocab)
    entities = []
    for sentence in doc.sents:
        for span in sentence.spans:
            ent = NamedEntity(
                text=span.text,
                type=span.type,
                norm=span.normal,
                sentence=sentence.text)
            entities.append(ent)
    return entities


def get_title(text: str) -> str:
    """Генеарция заголовка

    Args:
        text ([str]): Текста поста

    Returns:
        [str]: Заголовок
    """
    text = text.replace('\n', '.').replace('..', '.')
    text = preprocess_text(text)
    sents = list(sentenize(text))
    if len(sents[0].text) > 0:
        title = sents[0].text
    elif len(sents) > 2:
        title = sents[1].text
    else:
        title = '(без заголовка)'
    if len(title.split(',')[0].replace('.', '').split()) == 1:
        return title.replace('.', '')
    return title.split(',')[0].replace('.', '')


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


def remove_emoji(string: str) -> str:
    """https://gist.github.com/slowkow/7a7f61f495e3dbb7e3d767f97bd7304b#gistcomment-3315605
    """
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


def preprocess_text(text: str) -> str:
    text = str(text)
    if len(text) == 0:
        return '(без текста)'
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\xa0', ' ')
    text = text.replace('**', '')
    text = text.replace('__', '')
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
    text = text.replace('](', ' ').replace('[', ' ').replace(']', '')
    # club148281938|AromaTOCHKA
    text = re.sub(r'id\d+\|', '', text, flags=re.MULTILINE)
    text = text.replace('\u200b', '')
    text = remove_emoji(text)
    text = re.sub(r' +', ' ', text, flags=re.MULTILINE)
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
