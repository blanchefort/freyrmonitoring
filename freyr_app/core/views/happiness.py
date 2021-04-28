import os
import json
import pandas as pd
import numpy as np
import requests
import datetime
import configparser
from excel_response import ExcelResponse
from django.contrib.auth.decorators import login_required
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


@login_required
def index(request):
    """Индекс счастья региона
    """
    center_a, center_b = get_center()

    if request.method == 'POST':
        start_date, end_date = request.POST.get('daterange').split(' - ')
        start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y")
        end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y")
        category = int(request.POST.get('category'))
        map_type = request.POST.get('map_type')
    else:
        end_date = timezone.now() - datetime.timedelta(days=1)
        start_date = timezone.now() - datetime.timedelta(days=30)
        category = 0
        map_type = 'freyr'

    if category == 0:
        chart_name = 'Индекс для всего региона по всем категориям'
    else:
        chart_name = f'Индекс для всего региона по категории «{Category.objects.get(pk=category).name}»'

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
        'show_external': True if Happiness.objects.filter(source_type=1).count() > 0 else False,
        'chart_name': chart_name,
        'map_type': map_type
    }
    return TemplateResponse(request, 'happiness.html', context=context)


#@cache_page(3600 * 24)
@login_required
def leaflet_map(request, category: int, start_date: str, end_date: str, map_type: str):
    """Карта

    Args:
        category (int): Идентифкатор категории
        start_date (str): Начальная дата
        end_date (str): Конечная дата
    """
    data_path = os.path.join(settings.ML_MODELS, 'region.geojson')
    with open(data_path) as fp:
        geodata = json.load(fp)

    start_date = datetime.datetime.strptime(start_date, "%d.%m.%Y")
    end_date = datetime.datetime.strptime(end_date, "%d.%m.%Y")
    if Category.objects.filter(pk=category).count() == 0:
        for f in geodata['features']:
            district = District.objects.get(name=f['properties']['russian_name'])

            if map_type == 'external':
                nps = external_report(district, 0)
                f['properties']['nps'] = str(nps)
            elif map_type == 'freyr':
                nps, _, _, _ = calculate_happiness_by_district(district, (start_date, end_date))
                if round(nps, 3) == 5.00:
                    nps = np.nan
                f['properties']['nps'] = str(round(nps, 3))
            elif map_type == 'weighted':
                nps, _, _, _ = calculate_happiness_by_district(district, (start_date, end_date))
                external = external_report(district, 0)
                nps = (nps * .2) + (external * .8)
                f['properties']['nps'] = str(round(nps, 3))
    else:
        category = Category.objects.get(pk=category)
        for f in geodata['features']:
            district = District.objects.get(name=f['properties']['russian_name'])
            if map_type == 'external':
                nps = external_report(district, category)
                f['properties']['nps'] = str(nps)
            elif map_type == 'freyr':
                nps, _, _, _ = calculate_happiness(district, category, (start_date, end_date))
                if round(nps, 3) == 5.00:
                    nps = np.nan
                f['properties']['nps'] = str(round(nps, 3))
            elif map_type == 'weighted':
                nps, _, _, _ = calculate_happiness(district, category, (start_date, end_date))
                external = external_report(district, category)
                nps = (nps * .2) + (external * .8)
                f['properties']['nps'] = str(round(nps, 3))

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
    """Индекс
    """
    results = []
    mean_index = 0
    districts = District.objects.exclude(name='region')
    if Category.objects.filter(pk=category).count() == 0:
        for district in districts:
            nps, pos, neg, neu = calculate_happiness_by_district(district, (start_date, end_date))
            mean_index += nps
            if round(nps, 3) == 5.000:
                nps = 0
            # индекс из внешнего отчёта
            ext_district_happiness = external_report(district, category=0)
            # Глупая формула Ульяновска
            weighted_happiness = (nps * .2) + (ext_district_happiness * .8)
            results.append({
                'district': district,
                'nps': str(nps),
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'external_report': ext_district_happiness,
                'weighted_happiness': weighted_happiness,
            })
    else:
        category = Category.objects.get(pk=category)
        for district in districts:
            nps, pos, neg, neu = calculate_happiness(district, category, (start_date, end_date))
            mean_index += nps
            if round(nps, 3) == 5.000:
                nps = 0
            # индекс из внешнего отчёта
            ext_district_happiness = external_report(district, category)
            # Глупая формула Ульяновска
            weighted_happiness = (nps * .2) + (ext_district_happiness * .8)
            results.append({
                'district': district,
                'nps': str(nps),
                'pos': pos,
                'neg': neg,
                'neu': neu,
                'external_report': ext_district_happiness,
                'weighted_happiness': weighted_happiness,
            })
    return round(mean_index/len(districts), 3), results


def external_report(district, category):
    """
    Сторонний отчёт
    """
    value = 0
    if category == 0:
        values = Happiness.objects.filter(district=district).filter(source_type=1)
    else:
        values = Happiness.objects.filter(district=district).filter(source_type=1).filter(category=category)
    if len(values) == 0:
        return value
    for v in values:
        value += v.value
    value /= len(values)
    return value



@login_required
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


@login_required
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
                # Удалим предыдущий отчёт
                Happiness.objects.filter(source_type=1).exclude(name=request.POST['name']).delete()
        else:
            messages.error(request, 'Файл не загружен!')
    else:
        form = UploadHappinessIndex()

    context.update({'form': form})


    reports = set(h.name for h in Happiness.objects.filter(source_type=1))
    context.update({'reports': reports})

    return TemplateResponse(request, 'happiness_add.html', context=context)


@login_required
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
