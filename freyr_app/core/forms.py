from django import forms

class AddUrlForm(forms.Form):
    """Добавляем УРЛ для проверки
    """
    url = forms.URLField(initial='https://', label='Введите ссылку для проверки')

class UploadHappinessIndex(forms.Form):
    """Форма для загрузки файла с кастомным индексом счастья
    """
    name = forms.CharField(max_length=256, label='Название отчёта')
    file = forms.FileField(label='CSV-файл с отчётом')

class SearchItem(forms.Form):
    """Поиск по проиндексированным материалам
    """
    search_query = forms.CharField(max_length=512, label='✨✨✨Поиск!')
