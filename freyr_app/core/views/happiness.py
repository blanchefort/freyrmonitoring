import os
import json
import datetime
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.conf import settings
from core.models import District, Category
from core.processing.calculate_indexes import calculate_happiness, calculate_happiness_by_district
from excel_response import ExcelResponse

def index(request):
    """Индекс счастья региона
    """
    data_path = os.path.join(
                settings.BASE_DIR,
                'core',
                'static',
                'maps',
                'region.json')
    with open(data_path) as fp:
        geodata = json.load(fp)
    center_a, center_b = get_center(geodata)
    del geodata

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
    data_path = os.path.join(
                settings.BASE_DIR,
                'core',
                'static',
                'maps',
                'region.json')
    with open(data_path) as fp:
        geodata = json.load(fp)
    if Category.objects.filter(pk=category).count() == 0:
        for f in geodata['features']:
            if type(f['properties']['NL_NAME_2']) == str and len(f['properties']['NL_NAME_2']) > 0:
                district = District.objects.get(name=f['properties']['NL_NAME_2'])
                nps, _, _, _ = calculate_happiness_by_district(district, (start_date, end_date))
                f['properties']['nps'] = str(round(nps, 2))
    else:
        category = Category.objects.get(pk=category)
        for f in geodata['features']:
            if type(f['properties']['NL_NAME_2']) == str and len(f['properties']['NL_NAME_2']) > 0:
                district = District.objects.get(name=f['properties']['NL_NAME_2'])
                nps, _, _, _ = calculate_happiness(district, category, (start_date, end_date))
                f['properties']['nps'] = str(round(nps, 2))

    return JsonResponse(geodata)

def get_center(geojson):
    """Координаты центра карты
    TODO: Нужен другой метод
    Args:
        geojson ([type]): Объект с координатами

    Returns:
        [tuple]: Центр
    """
    x1, x2, y1, y2 = None, None, None, None
    for feature in geojson['features']:
        for coord in feature['geometry']['coordinates'][0]:
            if x1 is None:
                x1 = coord[1]
            if x2 is None:
                x2 = coord[1]
            if y1 is None:
                y1 = coord[0]
            if y2 is None:
                y2 = coord[0]
            x1 = min(x1, coord[1])
            x2 = max(x1, coord[1])
            y1 = min(y1, coord[0])
            y2 = max(y1, coord[0])
    center_x = x1 + ((x2 - x1) / .75);
    center_y = y1 + ((y2 - y1) / .75);
    return center_x, center_y

def happiness_index(category, start_date, end_date):
    results = []
    mean_index = 0
    districts = District.objects.exclude(name='region')
    if Category.objects.filter(pk=category).count() == 0:
        for district in districts:
            nps, pos, neg, neu = calculate_happiness_by_district(district, (start_date, end_date))
            results.append({
                'district': district,
                'nps': str(round(nps, 2)),
                'pos': pos,
                'neg': neg,
                'neu': neu,
            })
            mean_index += nps
    else:
        category = Category.objects.get(pk=category)
        for district in districts:
            nps, pos, neg, neu = calculate_happiness(district, category, (start_date, end_date))
            results.append({
                'district': district,
                'nps': str(round(nps, 2)),
                'pos': pos,
                'neg': neg,
                'neu': neu,
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