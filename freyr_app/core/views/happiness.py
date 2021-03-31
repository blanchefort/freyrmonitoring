import os
import json
import pandas as pd
import numpy as np
import requests
import datetime
import configparser
from excel_response import ExcelResponse
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from ..models import District, Category, Happiness
from ..processing.calculate_indexes import calculate_happiness, calculate_happiness_by_district
from ..forms import UploadHappinessIndex
from django.db.models import Sum

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

    reports = set(h.name for h in Happiness.objects.filter(source_type=1))

    if len(reports) > 0:
        show_external_index = 1
        districts = District.objects.exclude(name='region')
        ext_districts = [d.name for d in districts]
        ext_happiness = []
        report = list(reports)[0]
        for d in districts:
            value = 0
            values = Happiness.objects.filter(district=d)
            for v in values:
                value += v.value
            value /= len(values)
            ext_happiness.append(value)
        results_for_table = []
        for r in results:
            r = float(r['nps'])
            if r < 0:
                r = 0
            results_for_table.append(r)
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
        'show_external_index': show_external_index,
        'ext_districts': ext_districts,
        'ext_happiness': ext_happiness,
        'results_for_table': results_for_table,
        'ext_name': report,
    }
    return TemplateResponse(request, 'happiness.html', context=context)


#@cache_page(3600 * 24)
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
            if round(nps, 2) == 5.00:
                nps = np.nan
            f['properties']['nps'] = str(round(nps, 2))
    else:
        category = Category.objects.get(pk=category)
        for f in geodata['features']:
            district = District.objects.get(name=f['properties']['russian_name'])
            nps, _, _, _ = calculate_happiness(district, category, (start_date, end_date))
            if round(nps, 2) == 5.00:
                nps = np.nan
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
            mean_index += nps
            if round(nps, 3) == 5.000:
                nps = '-1'
            else:
                nps = str(round(nps, 3))
            results.append({
                'district': district,
                'nps': nps,
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'ext_district_happiness': str(round(ext_district_happiness, 3))
            })
    else:
        category = Category.objects.get(pk=category)
        for district in districts:
            nps, pos, neg, neu = calculate_happiness(district, category, (start_date, end_date))
            if district.name in ext_districts:
                ext_idx = ext_districts.index(district.name)
                ext_district_happiness = ext_happiness[ext_idx]
            else:
                ext_district_happiness = 0
            mean_index += nps
            if round(nps, 3) == 5.000:
                nps = '-1'
            else:
                nps = str(round(nps, 3))
            results.append({
                'district': district,
                'nps': nps,
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'ext_district_happiness': str(round(ext_district_happiness, 3))
            })
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
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    ext_districts, ext_happiness = [], []
    if 'HAPPINESS_INDEX' in config:
        try:
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
        except:
            ext_districts, ext_happiness = [], []
    return ext_districts, ext_happiness


def upload_custom_data(request):
    """Загрузить собственные данные
    """
    context = {}
    if request.method == 'POST':
        form = UploadHappinessIndex(request.POST, request.FILES)
        if form.is_valid() and request.FILES['file']:
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            messages.success(request, f'Файл успешно загружен!')
            filename = os.path.join(settings.MEDIA_ROOT, filename)
            df = False
            try:
                df = pd.read_csv(filename, index_col='Муниципалитет')
            except:
                messages.error(request, 'Файл не может быть прочтён!')
            if df is not False:
                regions = District.objects.all()
                categories = Category.objects.exclude(name='Без темы')
                try:
                    for r in regions:
                        for c in categories:
                            value = df.loc[r.name, c.name]
                            Happiness(
                                source_type=1,
                                name=request.POST['name'],
                                district=r,
                                category=c,
                                value=float(value),
                            ).save()
                except:
                    Happiness.objects.filter(name=request.POST['name']).delete()
                    messages.error(request, f'Парсинг файла не удался, проверьте, ести ли муниципалитет {r} и категория {c}')
        else:
            messages.error(request, 'Файл не загружен!')
    else:
        form = UploadHappinessIndex()

    context.update({'form': form})


    reports = set(h.name for h in Happiness.objects.filter(source_type=1))
    context.update({'reports': reports})

    return TemplateResponse(request, 'happiness_add.html', context=context)


def example_csv(request):
    """Возвращаем файл-пример для кастомного индекса счастья
    """
    regions = District.objects.all()
    categories = Category.objects.exclude(name='Без темы')
    example_df = pd.DataFrame(regions, columns=['Муниципалитет'])
    for c in categories:
        example_df[c] = [0]*len(example_df)
    example_df_path = os.path.join(settings.STATIC_ROOT, 'example_df.csv')
    example_df.to_csv(example_df_path, index=False)

    response = HttpResponse(
        open(example_df_path).read(),
        content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="example_df.csv"'
    return response
