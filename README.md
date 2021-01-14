# FreyrMonitoring
*Мониторинг общественного мнения в интернете*

## Установка

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
Komi
Ingush
Rostov
Sakhalin
Moscow City
Kaluga
Moskva
Astrakhan'
Karelia
Lipetsk
Tatarstan
City of St. Petersburg
Krasnodar
Yaroslavl'
Buryat
Perm'
Kalmyk
Murmansk
Adygey
Ryazan'
Voronezh
Tula
Yamal-Nenets
Orenburg
Ul'yanovsk
Kirov
Maga Buryatdan
Bryansk
Saratov
Arkhangel'sk
Altay
Kostroma
Mordovia
Kemerovo
Ivanovo
Karachay-Cherkess
North Ossetia
Nenets
Vologda
Khanty-Mansiy
Tver'
Pskov
Kurgan
Kaliningrad
Mariy-El
Tomsk
Nizhegorod
Chechnya
Vladimir
Volgograd
Novosibirsk
Khabarovsk
Dagestan
Sakha
Kamchatka
Yevrey
Irkutsk
Stavropol'
Belgorod
Sverdlovsk
Smolensk
Khakass
Penza
Tyumen'
Leningrad
Gorno-Altay
Udmurt
Novgorod
Tuva
Amur
Zabaykal'ye
Chukot
Bashkortostan
Chuvash
Chelyabinsk
Krasnoyarsk
Omsk
Kabardin-Balkar
Tambov
Orel
Kursk
Samara
Primor'ye
```

* `[POSTGRES]`: Настоятельно рекомендуется использовать БД PostgreSQL. Но если вы хотите лишь посмотреть, как работает система, можно не использовать данную базу данных. Просто удалите этот пункт, и система будет использовать SQLite.

#### 2.1. Установить часовой пояс:

В файле `freyr_app/settings.py` строка:

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
python manage.py download_models
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