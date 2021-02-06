import os, shutil
import wget
import requests
from bs4 import BeautifulSoup
import pandas as pd
import osmnx as ox
import logging
import configparser
from transformers import BertTokenizer
from transformers import BertForSequenceClassification
from django.conf import settings
from core.models import District, ArticleDistrict
logger = logging.getLogger(__name__)

federal_subjects_index_path = 'https://www.dropbox.com/s/dsac9n9xcqbwob4/federal_subjects_index.csv?dl=1'
freyr_region_graphs = (
    'https://www.dropbox.com/s/s4fi81ymh2f2tmj/fias_99.edgelist?dl=1',
    'https://www.dropbox.com/s/h77qhpu3g32dhhr/fias_91.edgelist?dl=1',
    'https://www.dropbox.com/s/ewlmpwwwy730vpa/fias_87.edgelist?dl=1',
    'https://www.dropbox.com/s/3nhcckfvcfx6ual/fias_86.edgelist?dl=1',
    'https://www.dropbox.com/s/ocl2zi29anusakd/fias_83.edgelist?dl=1',
    'https://www.dropbox.com/s/x1oedy04mfx24n6/fias_79.edgelist?dl=1',
    'https://www.dropbox.com/s/k7nb98lsz0ha5v8/fias_76.edgelist?dl=1',
    'https://www.dropbox.com/s/hl7prbfkcpq0iyk/fias_75.edgelist?dl=1',
    'https://www.dropbox.com/s/iydb1yj3uk6fxwe/fias_73.edgelist?dl=1',
    'https://www.dropbox.com/s/s5bz8uo4r9nqxhi/fias_72.edgelist?dl=1',
    'https://www.dropbox.com/s/5kjn5v3aihxrxgv/fias_71.edgelist?dl=1',
    'https://www.dropbox.com/s/86elytu6h1ldvhr/fias_70.edgelist?dl=1',
    'https://www.dropbox.com/s/cfhr8gvxgqaa8n9/fias_68.edgelist?dl=1',
    'https://www.dropbox.com/s/f4xn0kpad9nuztu/fias_67.edgelist?dl=1',
    'https://www.dropbox.com/s/jk58gzcot36rpfw/fias_65.edgelist?dl=1',
    'https://www.dropbox.com/s/svu38lulgkscchx/fias_62.edgelist?dl=1',
    'https://www.dropbox.com/s/317em00y8jsvz6m/fias_61.edgelist?dl=1',
    'https://www.dropbox.com/s/j3yuxk7bt5y9gt0/fias_60.edgelist?dl=1',
    'https://www.dropbox.com/s/e4pd5i6ndrwzzkt/fias_58.edgelist?dl=1',
    'https://www.dropbox.com/s/knnpa5dl830067g/fias_57.edgelist?dl=1',
    'https://www.dropbox.com/s/7bj43k5m5u9jf3n/fias_55.edgelist?dl=1',
    'https://www.dropbox.com/s/acm6ztu4lbeekbi/fias_53.edgelist?dl=1',
    'https://www.dropbox.com/s/1b9posmlbse19fz/fias_52.edgelist?dl=1',
    'https://www.dropbox.com/s/lpxngn6ti4bht06/fias_49.edgelist?dl=1',
    'https://www.dropbox.com/s/47aguh1ln2l7nxu/fias_48.edgelist?dl=1',
    'https://www.dropbox.com/s/9axable6blhrotv/fias_46.edgelist?dl=1',
    'https://www.dropbox.com/s/ceqn21i215d5fdi/fias_44.edgelist?dl=1',
    'https://www.dropbox.com/s/rjp3fdlypn2rloi/fias_41.edgelist?dl=1',
    'https://www.dropbox.com/s/gqasm1adxp7kx44/fias_40.edgelist?dl=1',
    'https://www.dropbox.com/s/n0gq1mqbdujr4o8/fias_39.edgelist?dl=1',
    'https://www.dropbox.com/s/7v4fb77xp87co5g/fias_38.edgelist?dl=1',
    'https://www.dropbox.com/s/phkxw5hxf1qnk8p/fias_37.edgelist?dl=1',
    'https://www.dropbox.com/s/i5ebg89ffwb0pl4/fias_35.edgelist?dl=1',
    'https://www.dropbox.com/s/w05ltywhz90t4y0/fias_34.edgelist?dl=1',
    'https://www.dropbox.com/s/k8u95llpvo3ylkd/fias_33.edgelist?dl=1',
    'https://www.dropbox.com/s/6ie8j6souua81m2/fias_32.edgelist?dl=1',
    'https://www.dropbox.com/s/v3yj224ghpzi58n/fias_30.edgelist?dl=1',
    'https://www.dropbox.com/s/y2j1od86so1dq8n/fias_28.edgelist?dl=1',
    'https://www.dropbox.com/s/fsy5hy0iw0v9mh1/fias_25.edgelist?dl=1',
    'https://www.dropbox.com/s/8g0jgjvf7kb4ixb/fias_24.edgelist?dl=1',
    'https://www.dropbox.com/s/mzzhbue62x66dh6/fias_21.edgelist?dl=1',
    'https://www.dropbox.com/s/kgd5gprjfhvayr4/fias_20.edgelist?dl=1',
    'https://www.dropbox.com/s/rbr1c2o11e0bvfu/fias_19.edgelist?dl=1',
    'https://www.dropbox.com/s/crl5miw76u1g6dx/fias_18.edgelist?dl=1',
    'https://www.dropbox.com/s/q85qqlhe8j63xhf/fias_17.edgelist?dl=1',
    'https://www.dropbox.com/s/bq7tcqgs1w5lsg7/fias_15.edgelist?dl=1',
    'https://www.dropbox.com/s/o2pziu8sx0itfys/fias_13.edgelist?dl=1',
    'https://www.dropbox.com/s/7fjn8tw2ijh9f2o/fias_12.edgelist?dl=1',
    'https://www.dropbox.com/s/nb5q3u1ze18ctzd/fias_11.edgelist?dl=1',
    'https://www.dropbox.com/s/74mes123h9cv12g/fias_10.edgelist?dl=1',
    'https://www.dropbox.com/s/5306zqc4c47sqyd/fias_09.edgelist?dl=1',
    'https://www.dropbox.com/s/i1l3dp0fmvb5jo0/fias_08.edgelist?dl=1',
    'https://www.dropbox.com/s/3ne2xtca5xi85q4/fias_07.edgelist?dl=1',
    'https://www.dropbox.com/s/9orhmheejo0rf54/fias_06.edgelist?dl=1',
    'https://www.dropbox.com/s/n3vt1b8j5sd03wo/fias_05.edgelist?dl=1',
    'https://www.dropbox.com/s/dvemxjpge5hj83k/fias_04.edgelist?dl=1',
    'https://www.dropbox.com/s/9q04vrgkknx54p9/fias_03.edgelist?dl=1',
    'https://www.dropbox.com/s/41mbyprhuf3v13l/fias_01.edgelist?dl=1',
    'https://www.dropbox.com/s/scsgpz2nmgjbgnb/fias_66.edgelist?dl=1'
)

freyr_files = [
    {'save_path': 'article_sentiment', 'file_name': 'config.json',
     'url': 'https://www.dropbox.com/s/xppp7h47nvvpm5c/config.json?dl=1',},
    {'save_path': 'article_sentiment', 'file_name': 'pytorch_model.bin',
     'url': 'https://www.dropbox.com/s/sg7h06va70ikenb/pytorch_model.bin?dl=1',},
    {'save_path': 'article_theme', 'file_name': 'config.json',
     'url': 'https://www.dropbox.com/s/plsxvqk6aj052t1/config.json?dl=1',},
    {'save_path': 'article_theme', 'file_name': 'pytorch_model.bin',
     'url': 'https://www.dropbox.com/s/as8nrz5y8ubcbua/pytorch_model.bin?dl=1',},
    {'save_path': 'gov_categories', 'file_name': 'classifier.pt',
     'url': 'https://www.dropbox.com/s/knjbpwxj7vcizcf/classifier.pt?dl=1',},
    {'save_path': '', 'file_name': 'stopwords.txt',
     'url': 'https://www.dropbox.com/s/regobpg4xciezt6/stopwords.txt?dl=1',},
    {'save_path': '', 'file_name': 'ru_bert_config.json',
     'url': 'https://www.dropbox.com/s/02ih472utx9gcex/ru_bert_config.json?dl=1',},
    {'save_path': 'article_appeal', 'file_name': 'config.json',
     'url': 'https://www.dropbox.com/s/7o1fz3mow8o7zh6/config.json?dl=1',},
    {'save_path': 'article_appeal', 'file_name': 'pytorch_model.bin',
     'url': 'https://www.dropbox.com/s/plp0k4934yome64/pytorch_model.bin?dl=1',}
]
ML_NAMES = (
    'article_sentiment',
    'article_theme',
    'gov_categories',
    'article_appeal',
    'comment_sentiment',
    'addenda', # стоп-слова и Берт-конфиг
)
def osm_get_info(idx):
    """Получаем информацию об административной территории
    """
    link = 'https://www.openstreetmap.org/api/0.6/relation/' + str(idx)
    response = requests.get(link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')
        subarea_ids = [member.get('ref') for member in soup.find_all('member', {'role':'subarea'})]
        name = soup.find('tag', {'k': 'name'})
        name = name.get('v')
        return name, subarea_ids
    return False


def geography():
    """Устанавливаем необходимые данные для работы с географией:
    - в БД заносим данные по муниципалитетам.
    - сохраняем карту в GEOJSON
    - сохраняем граф географических названий"""
    District.objects.all().delete()
    ArticleDistrict.objects.all().delete()
    # Качаем файл с регионами
    logger.info('Скачиваем данные по регионам России')
    file_path = os.path.join(settings.ML_MODELS, 'federal_subjects_index.csv')
    wget.download(federal_subjects_index_path, file_path)
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_PATH)
    federal_subjects_index = pd.read_csv(file_path)
    region = config['REGION']['NAME']
    if region not in federal_subjects_index.name.to_list():
        logger.error('Данных для региона с данным кодом не найдено. \
        Проверьте правильность написания региона, либо обратитесь за \
        помощью к разработчику: https://tlgg.ru/blanchefort')
        return False
    idx = int(federal_subjects_index[federal_subjects_index.name == region].idx)
    _, disctict_ids = osm_get_info(idx)
    district_names = []
    extended_names = []
    for i in disctict_ids:
        dist_name, _ = osm_get_info(i)
        district_names.append(dist_name)
        extended_names.append(dist_name + ', ' + region + ', Россия')
    logger.info('Сохраняем муниципалитеты в базу данных')
    District.objects.create(name='region')
    for dist_name in district_names:
        District.objects.create(name=dist_name)

    logger.info('Формируем карту всего региона')
    region_geo = ox.geocode_to_gdf(extended_names)
    region_geo['russian_name'] = district_names
    file_path = os.path.join(settings.ML_MODELS, 'region.geojson')
    region_geo.to_file(file_path, driver='GeoJSON')
    # Граф адресов региона
    # TODO: Пересобрать граф
    fname = f"fias_{config['REGION']['CODE']}"
    selected_file = None
    for flink in freyr_region_graphs:
        if fname in flink:
            selected_file = flink
            break
    if selected_file is None:
        logger.error(
            'Данных для региона с данным кодом не найдено. \
            Проверьте правильность написания кода региона, \
            либо обратитесь за помощью к разработчику: https://tlgg.ru/blanchefort')
        return False
    logger.info('Сохраняем граф адресов региона')
    file_path = os.path.join(settings.ML_MODELS, 'geograph.edgelist')
    wget.download(selected_file, file_path)

    logger.info('Геоданные для региона полностью собраны!')
    return True


def download_freyr_model(name: str):
    """Качаем собственную модель"""
    for ff in freyr_files:
        if name == ff['save_path']:
            logger.info(f"Download model: {ff['save_path']}")
            save_path = os.path.join(settings.ML_MODELS, ff['save_path'])
            file_path = os.path.join(save_path, ff['file_name'])
            os.makedirs(save_path, exist_ok=True)
            if os.path.isfile(file_path):
                os.remove(file_path)
            wget.download(ff['url'], file_path)
            logger.info('')

    # Токенизаторы
    if name in ('article_theme', 'article_sentiment'):
        BertTokenizer.from_pretrained(
            'DeepPavlov/rubert-base-cased-conversational').save_pretrained(
            os.path.join(settings.ML_MODELS, 'rubert-base-cased-conversational-tokenizer'))

    if name == 'gov_categories':
        BertTokenizer.from_pretrained(
            'DeepPavlov/rubert-base-cased').save_pretrained(
            os.path.join(settings.ML_MODELS, 'rubert-base-cased-tokenizer'))

    if name == 'article_appeal':
        BertTokenizer.from_pretrained(
            'DeepPavlov/rubert-base-cased-conversational').save_pretrained(
            os.path.join(settings.ML_MODELS, 'rubert-base-cased-conversational-tokenizer'))

    if name == 'comment_sentiment':
        logger.info(f'Download Sentiment Models')
        for m_name in ('rubert-base-cased-sentiment', 'rubert-base-cased-sentiment-rusentiment'):
            BertForSequenceClassification.from_pretrained(
                f'blanchefort/{m_name}').save_pretrained(
                os.path.join(settings.ML_MODELS, m_name))
            BertTokenizer.from_pretrained(
                f'blanchefort/{m_name}').save_pretrained(
                os.path.join(settings.ML_MODELS, m_name))

    if name == 'addenda':
        for ff in freyr_files:
            if ff['save_path'] == '':
                save_path = os.path.join(settings.ML_MODELS, ff['save_path'])
                file_path = os.path.join(save_path, ff['file_name'])
                os.makedirs(save_path, exist_ok=True)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                wget.download(ff['url'], file_path)


def download_kaldi():
    """Качаем и распаковываем Кальди"""
    logger.info(f'Download Kaldi')
    m_name = 'vosk-model-ru-0.10'
    wget.download(
        f'https://alphacephei.com/vosk/models/{m_name}.zip',
        os.path.join(settings.ML_MODELS, f'{m_name}.zip')
    )
    logger.info(f'Extracting Kaldi model files')
    shutil.unpack_archive(
        os.path.join(settings.ML_MODELS, f'{m_name}.zip')
    )

    if os.path.isdir(settings.KALDI):
        shutil.rmtree(settings.KALDI, ignore_errors=True)
    os.rename(m_name, settings.KALDI)
    os.remove(os.path.join(settings.ML_MODELS, f'{m_name}.zip'))


def recreate_dirs():
    """Создаём папки. Если они есть, удаляем"""
    logger.info('Create Dirs')
    if os.path.isdir(settings.AUDIO_PATH):
        shutil.rmtree(settings.AUDIO_PATH, ignore_errors=True)
    os.makedirs(settings.AUDIO_PATH, exist_ok=True)
    if os.path.isdir(settings.ML_MODELS):
        shutil.rmtree(settings.ML_MODELS, ignore_errors=True)
    if not os.path.isdir(settings.CLUSTERS_PATH):
        os.makedirs(settings.CLUSTERS_PATH, exist_ok=True)