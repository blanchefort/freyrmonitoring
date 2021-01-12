from django.contrib import admin

from .models import (
    Site,
    Article,
    Entity,
    EntityLink,
    Theme,
    ThemeArticles,
    ThemeMarkup,
    Comment,
    Category,
    ArticleCategory
)

from import_export import resources
from import_export.admin import ImportExportModelAdmin

class ArticleResource(resources.ModelResource):
    class Meta:
        model = Article

class EntityResource(resources.ModelResource):
    class Meta:
        model = Entity

class CommentResource(resources.ModelResource):
    class Meta:
        model = Comment

class ArticleAdmin(ImportExportModelAdmin):
    resource_class = ArticleResource
    list_display = ('title',  'publish_date', 'theme', 'sentiment')
    date_hierarchy = 'publish_date'

class EntityAdmin(ImportExportModelAdmin):
    resource_class = EntityResource

class CommentAdmin(ImportExportModelAdmin):
    resource_class = CommentResource
    list_display = ('publish_date', 'text', 'sentiment')

admin.site.register(Site)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityLink)
admin.site.register(Theme)
admin.site.register(ThemeArticles)
admin.site.register(ThemeMarkup)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category)
admin.site.register(ArticleCategory)