# Команды

## Запуск веб-интерфейса

`$ python manage.py runserver 0:5001`

## Запуск краулера

`$ python manage.py crawler`

## Скачивание моделей

`$ python manage.py download_models --full` Полное обновление всех моделей системы

`$ python manage.py download_models --loyalty` Модели для индекса лояльности

`$ python manage.py download_models --categories` Модель для классификации категорий постов

`$ python manage.py download_models --appeal` Модель для выявления обращений граждан

`$ python manage.py download_models --comments` Модель для определения тональности комментариев

`$ python manage.py download_models --stopwords` Стоп-слова

`$ python manage.py download_models --kaldi` Модель для распознавания речи

`$ python manage.py download_models --geography` Наборы данных для работы с географией


## Пересчёт индекса

`$ python manage.py recalculate --appeals` Классификация постов-обращений, на которые требуется ответ

`$ python manage.py recalculate --titles` Переделать все заголовки, сгенерированные для текстов из соцсетей

`$ python manage.py recalculate --geo` Пересчёт привязки статей к муниципалитетам

`$ python manage.py recalculate --loyalty` Пересчитать индекс лояльности

`$ python manage.py recalculate --clustering` Новая кластеризация

`$ python manage.py recalculate --indexing` Пересборка индекса поиска

`$ python manage.py recalculate --ner` Пересборка именованных сущностей