# FreyrMonitoring
*Мониторинг общественного мнения в интернете*

## Установка

0. Установка производится на ОС Ubuntu >= 18.04 с оперативной памятью от 4 Гб. В системе должны быть предустановлены PostgreSQL и Kaldi.

1. Последовательно выполнить команды в терминале:

```
git clone https://github.com/blanchefort/freyrmonitoring.git
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Отредактировать файл `freyrmonitoring/freyr_app/config.ini.example` и сохранить его как `freyrmonitoring/freyr_app/config.ini`

3. Скачать ML-модели:

```
cd freyrmonitoring/freyr_app
python manage.py download_models
```

4. Настроить БД, установить статичные файлы и создать суперадминистратора:

```
python manage.py makemigrations core
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

5. Запуск development-версии:

Веб-интерфейс:

```
python manage.py runserver
```

Сборщик данных:

```
python manage.py crawler
```
