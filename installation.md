# Установка

#### 0. Установка производится на ОС Ubuntu >= 18.04 с оперативной памятью от 4 Гб. В системе должны быть предустановлены PostgreSQL, Kaldi, GDAL, ffmpeg.

#### 1. Последовательно выполнить команды в терминале:

```
git clone https://github.com/blanchefort/freyrmonitoring.git
python -m venv venv
source venv/bin/activate
cd freyrmonitoring
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Отредактировать файл `freyrmonitoring/freyr_app/config.ini.example` и сохранить его как `freyrmonitoring/freyr_app/config.ini`.

* `[ML]`: `BATCH_SIZE` - количество текстов для обработки нейросетями. Установите это значение в зависимости от объёма оперативной памяти вашего сервера. Чем больше памяти, тем большее количество текстов для обработки можно указать, и тем меньше времени понадобится на обработку всех текстов.

* `[REGION]`: Обратите внимание на то, как корректно назвать свой регион. Нужно выбрать значение из этого списка:

```
Чечня
Ставропольский край
Северная Осетия — Алания
Карачаево-Черкесия
Кабардино-Балкария
Ингушетия
Дагестан
Башкортостан
Татарстан
Оренбургская область
Кировская область
Пермский край
Удмуртия
Ульяновская область
Чувашия
Мордовия
Нижегородская область
Пензенская область
Саратовская область
Марий Эл
Самарская область
Курганская область
Свердловская область
Тюменская область
Ханты-Мансийский автономный округ — Югра
Челябинская область
Ямало-Ненецкий автономный округ
Республика Тыва
Томская область
Республика Хакасия
Омская область
Новосибирская область
Красноярский край
Кемеровская область
Иркутская область
Алтайский край
Республика Алтай
Чукотский автономный округ
Хабаровский край
Сахалинская область
Республика Саха (Якутия)
Приморский край
Магаданская область
Камчатский край
Еврейская автономная область
Амурская область
Забайкальский край
Республика Бурятия
Санкт-Петербург
Республика Коми
Республика Карелия
Псковская область
Новгородская область
Ненецкий автономный округ
Мурманская область
Ленинградская область
Калининградская область
Вологодская область
Архангельская область
Ростовская область
Краснодарский край
Республика Калмыкия
Волгоградская область
Астраханская область
Адыгея
Севастополь
Ярославская область
Тульская область
Тверская область
Тамбовская область
Смоленская область
Рязанская область
Орловская область
Московская область
Москва
Липецкая область
Курская область
Костромская область
Калужская область
Ивановская область
Воронежская область
Владимирская область
Брянская область
Белгородская область
```

* `[POSTGRES]`: Настоятельно рекомендуется использовать БД PostgreSQL. Но если вы хотите лишь посмотреть, как работает система, можно не использовать данную базу данных. Просто удалите этот пункт, и система будет использовать SQLite.

#### 2.1. Установить часовой пояс:

Посмотреть временные зоны можно здесь: https://www.timeserver.ru/

```python
TIME_ZONE = 'Europe/Moscow'
```

#### 3. Настроить БД:

```
cd freyrmonitoring/freyr_app
python manage.py makemigrations core
python manage.py migrate
```

#### 4. Скачать ML-модели и произвести дополнительные настройки системы под выбранный регион:

Периодически мы обновляем модели, улучшая их качество, поэтому иногда можно повторять эту операцию, чтобы получать свежие обновления.

```
python manage.py download_models --full
```

#### 5. Установить статичные файлы:

```
python manage.py collectstatic
```

#### 5.1. Если нужно, можно создать суперадминистратора:

```
python manage.py createsuperuser
```

#### 6. Запуск development-версии:

Веб-интерфейс:

```
python manage.py runserver
```

Сборщик данных:

```
python manage.py crawler
```

При первом запуске сборщика нужно будет ввести телефонный номер и код авторизации для Телеграма.