"""Команда для пересчёта собранных данных.
Полезна, когда вы установили улучшенные модели,
и хотите получить более точные данные.

Использование:

$python manage.py recalculate <--option>

Список доступных опций:

$ python manage.py recalculate --help
"""
import logging
from django.core.management.base import BaseCommand
from ._recalc_funcs import (
    titles,
    appeals, 
    geo, 
    loyalty, 
    clustering,
    indexing,
    ner)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Команда для пересчёта собранных данных. Полезна, когда \
    вы установили улучшенные модели, и хотите получить более точные данные.'

    def handle(self, *args, **options):
        if options['titles']:
            titles()
        if options['appeals']:
            appeals()
        if options['geo']:
            geo()
        if options['loyalty']:
            loyalty()
        if options['clustering']:
            clustering()
        if options['indexing']:
            indexing()
        if options['ner']:
            ner()

    def add_arguments(self, parser):
        commands = (
            ('--appeals', 'Классификация постов-обращений, на которые требуется ответ',),
            ('--titles', 'Переделать все заголовки, сгенерированные для текстов из соцсетей',),
            ('--geo', 'Пересчёт привязки статей к муниципалитетам',),
            ('--loyalty', 'Пересчитать индекс лояльности',),
            ('--clustering', 'Новая кластеризация.',),
            ('--indexing', 'Пересборка индекса поиска'),
            ('--ner', 'Пересборка именованных сущностей'),
        )
        for command, help in commands:
            parser.add_argument(
                command,
                action='store_true',
                default=False,
                help=help
            )