import os
import json
import pandas as pd
import requests
import datetime
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.conf import settings
from core.models import District, Category
from core.processing.calculate_indexes import calculate_happiness, calculate_happiness_by_district
from excel_response import ExcelResponse
import configparser


def index(request):
    """Индекс счастья региона
    """
    center_a, center_b = get_center()

    if request.method == 'POST':
        start_date, end_date = request.POST.get('daterange').split(' - ')
        start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y")
        end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y")
        category = int(request.POST.get('category'))
    else:
        end_date = timezone.now() - datetime.timedelta(days=1)
        start_date = timezone.now() - datetime.timedelta(days=30)
        category = 0

    mean_index, results = happiness_index(category, start_date, end_date)

    start_date = str(start_date.day) + '.' + str(start_date.month) + '.' + str(start_date.year)
    end_date = str(end_date.day) + '.' + str(end_date.month) + '.' + str(end_date.year)
    context = {
        'page_title': 'Индекс удовлетворённости жизнью',
        'categories': Category.objects.exclude(name='Без темы'),
        'start_date': start_date,
        'end_date': end_date,
        'results': results,
        'center_a': str(center_a),
        'center_b': str(center_b),
        'mean_index': mean_index,
        'selected_cat': category,
    }
    return TemplateResponse(request, 'happiness.html', context=context)


def leaflet_map(request, category: int, start_date: str, end_date: str):
    """Карта

    Args:
        category (int): Идентифкатор категории
        start_date (str): Начальная дата
        end_date (str): Конечная дата
    """
    start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
    end_date = datetime.datetime.strptime(end_date, "%d.%m.%Y")
    data_path = os.path.join(settings.ML_MODELS, 'region.geojson')
    with open(data_path) as fp:
        geodata = json.load(fp)
    if Category.objects.filter(pk=category).count() == 0:
        for f in geodata['features']:
            district = District.objects.get(name=f['properties']['russian_name'])
            nps, _, _, _ = calculate_happiness_by_district(district, (start_date, end_date))
            f['properties']['nps'] = str(round(nps, 2))
    else:
        category = Category.objects.get(pk=category)
        for f in geodata['features']:
            district = District.objects.get(name=f['properties']['russian_name'])
            nps, _, _, _ = calculate_happiness(district, category, (start_date, end_date))
            f['properties']['nps'] = str(round(nps, 2))

    return JsonResponse(geodata)


def get_center():
    """Координаты центра карты

    Returns:
        [tuple]: Центр региона
    """
    file_path = os.path.join(settings.ML_MODELS, 'federal_subjects_index.csv')
    federal_subjects_index = pd.read_csv(file_path)
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    region = config['REGION']['NAME']
    lat = float(federal_subjects_index[federal_subjects_index.name == region].lat)
    lon = float(federal_subjects_index[federal_subjects_index.name == region].lon)
    lat -= 0.01*lat
    lon += 0.015*lon
    return lat, lon


def happiness_index(category, start_date, end_date):
    results = []
    mean_index = 0
    ext_districts, ext_happiness = external_happiness_index()
    districts = District.objects.exclude(name='region')
    if Category.objects.filter(pk=category).count() == 0:
        for district in districts:
            nps, pos, neg, neu = calculate_happiness_by_district(district, (start_date, end_date))
            if district.name in ext_districts:
                ext_idx = ext_districts.index(district.name)
                ext_district_happiness = ext_happiness[ext_idx]
            else:
                ext_district_happiness = 0
            results.append({
                'district': district,
                'nps': str(round(nps, 2)),
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'ext_district_happiness': str(round(ext_district_happiness, 3))
            })
            mean_index += nps
    else:
        category = Category.objects.get(pk=category)
        for district in districts:
            nps, pos, neg, neu = calculate_happiness(district, category, (start_date, end_date))
            if district.name in ext_districts:
                ext_idx = ext_districts.index(district.name)
                ext_district_happiness = ext_happiness[ext_idx]
            else:
                ext_district_happiness = 0
            results.append({
                'district': district,
                'nps': str(round(nps, 2)),
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'ext_district_happiness': str(round(ext_district_happiness, 3))
            })
            mean_index += nps
    return round(mean_index/len(districts), 2), results


def excelview(request, category: int, start_date: str, end_date: str):
    """Эксель-файл для выборки

    Args:
        category (int): категория
        start_date (str): начало периода
        end_date (str): конец периода
    """
    title = f'Индекс удовлетворённости жизнью {{start_date}} - {{end_date}}'
    start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
    end_date = datetime.datetime.strptime(end_date, "%d.%m.%Y")
    mean_index, results = happiness_index(category, start_date, end_date)
    data = []
    for item in results:
        data.append({
            'Муниципалитет': item['district'].name,
            'Объём положительных материалов': item['pos'],
            'Объём отрицательных материалов': item['neg'],
            'Объём нейтральных материалов': item['neu'],
            'Индекс удовлетворённости жизнью': float(item['nps']),
        })
    return ExcelResponse(data, title)

def external_happiness_index():
    """Индекс счастья внешний"""
    ext_districts, ext_happiness = [], []
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    if 'HAPPINESS_INDEX' in config:
        response = requests.get(config['HAPPINESS_INDEX']['LINK'])
        if response.status_code == 200:
            data = response.json()

            ext_districts = []
            for item in data['Наименование МО']:
                if data['Наименование МО'][item].startswith('г. '):
                    ext_districts.append(data['Наименование МО'][item].replace('г. ', 'городской округ '))
                else:
                    ext_districts.append(data['Наименование МО'][item])

            ext_happiness = list(data['Индекс счастья'].values())
    return ext_districts, ext_happiness
