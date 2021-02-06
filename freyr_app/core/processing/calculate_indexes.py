from django.db.models import Q
from ..models import Article, District, Category, Comment
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

    region = District.objects.get(name='region')
    articles = Article.objects \
        .filter(Q(article_district__district=district) | Q(article_district__district=region)) \
        .filter(publish_date__range=[start_date, end_date]) \
        .filter(categories__category=category)

    for article in articles:
        if article.happiness_sentiment == 1:
            positive_index.append(max(1, article.views))
        if article.happiness_sentiment == 2:
            negative_index.append(max(1, article.views))
        if article.happiness_sentiment == 0:
            neutral_index.append(max(1, article.views))
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

    for article in articles:
        if article.happiness_sentiment == 1:
            positive_index.append(max(1, article.views))
        if article.happiness_sentiment == 2:
            negative_index.append(max(1, article.views))
        if article.happiness_sentiment == 0:
            neutral_index.append(max(1, article.views))
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


def nps_norm100(nps: float) -> float:
    """Переводим индекс NPS в шкалу 0..10

    Args:
        nps (float): Индекс

    Returns:
        float: Нормализованный индекс
    """
    data = [-100, 100, nps]
    data = (data - np.min(data)) / (np.max(data) - np.min(data))
    return data[-1]*100


def loyalty_index(year: int, month: int) -> float:
    """Индекс лояльности за определённый период

    NPS = # Promoters - # Detractors / # Votes * 100
    У нас:
    (pos - neg) / total * 100

    Args:
        year (int): Год
        month (int): Месяц

    Returns:
        float: Нормализованный индекс 0..100
    """
    total = Article.objects.filter(theme=True) \
        .filter(publish_date__year=year, publish_date__month=month) \
        .count() + 1e-8
    pos = Article.objects.filter(theme=True) \
        .filter(publish_date__year=year, publish_date__month=month) \
        .filter(sentiment=1).count()
    neg = Article.objects.filter(theme=True) \
        .filter(publish_date__year=year, publish_date__month=month) \
        .filter(sentiment=2).count()

    loyalty = pos - neg
    loyalty /= total
    loyalty *= 100
    loyalty = nps_norm100(loyalty)
    return loyalty
