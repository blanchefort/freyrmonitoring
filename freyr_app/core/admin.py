from django.contrib import admin

from .models.site import Site
from .models.article import Article
from .models.entity import Entity, EntityLink
from .models.theme import Theme, ThemeArticles

admin.site.register(Site)
#admin.site.register(Article)
admin.site.register(Entity)
admin.site.register(EntityLink)
admin.site.register(Theme)
admin.site.register(ThemeArticles)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title',  'publish_date', 'theme', 'sentiment')
    date_hierarchy = 'publish_date'
