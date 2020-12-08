from django import forms

class AddUrlForm(forms.Form):
    """Добавляем УРЛ для проверки
    """
    url = forms.URLField(initial='https://', label='Введите ссылку для проверки')