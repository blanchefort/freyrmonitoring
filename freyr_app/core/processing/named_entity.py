from dataclasses import dataclass
from ..models import Article


@dataclass
class NaimedEntity:
    """Объект именованной сущности для обработки её конвейером алгоритмов

    text: str - Сущность
    type: str - тип сущности
    article_link - ссылка на статью, из которой извлечена сущность
    lemma: str - лемматизированный вид сущности
    norm: str - нормализованный вид сущности
    sentence: str - предложение, в котором встретиласть сущность
    is_real: bool - Правильно распознана сущность или нет
    sentiment: - Тональность сущности

    """
    text: str
    type: str
    article_link: Article = None
    lemma: str = ''
    norm: str = ''
    sentence: str = ''
    is_real: bool = True
    sentiment: int = 0
