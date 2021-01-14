from django.db.models import Q
from core.models import Article, District, Category, Comment
import numpy as np

def calculate_happiness(district: District, category: Category, period: tuple) -> tuple:
    """Рассчёт субъективной удовлетворенность людей жизнью

    Args:
        district (District): Объект муниципалитета
        period (tuple(start_date, end_date)): Период, за который формируется индекс, 
        кортеж из datetime.datetime
            * start_date - начало периода
            * end_date - конец периода

        category (Category): Объект категории, для которой нужно сформировать индекс

    Returns:
        tuple: Индекс, количество комментариев
    """
    start_date, end_date = period
    positive_index, negative_index, neutral_index = [], [], []

    articles = Article.objects.filter(article_district__district=district)\
        .filter(categories__category=category)\
        .filter(publish_date__range=[start_date, end_date])
    
    for article in articles:
        positive_index.append(Comment.objects.filter(article=article).filter(sentiment=1).count())
        negative_index.append(Comment.objects.filter(article=article).filter(sentiment=2).count())
        neutral_index.append(Comment.objects.filter(article=article).filter(sentiment=0).count())
    
    nps = calculate_nps(positive_index, negative_index, neutral_index)
    return nps_norm10(nps), sum(positive_index), sum(negative_index), sum(neutral_index)

def calculate_happiness_by_district(district: District, period: tuple) -> tuple:
    """Рассчёт субъективной удовлетворенность людей жизнью по району

    Args:
        district (District): Объект муниципалитета
        period (tuple(start_date, end_date)): Период, за который формируется индекс, 
        кортеж из datetime.datetime
            * start_date - начало периода
            * end_date - конец периода

    Returns:
        tuple: Индекс, количество комментариев
    """
    start_date, end_date = period
    positive_index, negative_index, neutral_index = [], [], []

    region = District.objects.get(name='region')
    articles = Article.objects\
        .filter(Q(article_district__district=district) | Q(article_district__district=region))\
        .filter(publish_date__range=[start_date, end_date])
    
    positive_index.append(articles.filter(sentiment=1).count()*10)
    negative_index.append(articles.filter(sentiment=2).count()*10)
    neutral_index.append(articles.filter(sentiment=0).count()*10)
    for article in articles:
        positive_index.append(Comment.objects.filter(article=article).filter(sentiment=1).count())
        negative_index.append(Comment.objects.filter(article=article).filter(sentiment=2).count())
        neutral_index.append(Comment.objects.filter(article=article).filter(sentiment=0).count())
    
    nps = calculate_nps(positive_index, negative_index, neutral_index)
    return nps_norm10(nps), sum(positive_index), sum(negative_index), sum(neutral_index)

def calculate_nps(pos: list, neg: list, neu: list) -> float:
    """Считаем Net Promoter Score

    Args:
        pos (list): Список позитивных оценок
        neg (list): Список негативных оценок
        neu (list): Список нейтральных оценок

    Returns:
        float: NPS
    """
    pos = sum(pos)
    neg = sum(neg)
    neu = sum(neu)
    total = pos + neg + neu + 1e-8
    nps = pos - neg
    nps /= total
    nps *= 100
    return nps

def nps_norm10(nps: float) -> float:
    """Переводим индекс NPS в шкалу 0..10

    Args:
        nps (float): Индекс

    Returns:
        float: Нормализованный индекс
    """
    data = [-100, 100, nps]
    data = (data - np.min(data)) / (np.max(data) - np.min(data))
    return data[-1]*10