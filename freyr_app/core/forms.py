from django import forms
from .models.site import Site

class SiteForm(forms.ModelForm):
    """Форма площадки
    """
    class Meta:
        model = Site
        fields = ('url', 'title')
    
    def check_url(self):
        url = self.cleaned_data.get('url')
        if Site.objects.filter(url=url).exists():
            raise forms.ValidationError('Данный url уже в списке отслеживаемых.')
        return url