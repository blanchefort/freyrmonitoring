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
from ._recalc_funcs import titles, appeals, geo

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

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--appeals',
            action='store_true',
            default=False,
            help='Классификация постов-обращений, на которые требуется ответ'
        )
        parser.add_argument(
            '-t',
            '--titles',
            action='store_true',
            default=False,
            help='Переделать все заголовки, сгенерированные для текстов из соцсетей'
        )
        parser.add_argument(
            '-g',
            '--geo',
            action='store_true',
            default=False,
            help='Пересчёт привязки статей к муниципалитетам'
        )