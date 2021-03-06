from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

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
    ArticleCategory,
    District
)


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
    list_display = ('publish_date', 'title', 'theme', 'sentiment')
    date_hierarchy = 'publish_date'


class EntityAdmin(ImportExportModelAdmin):
    resource_class = EntityResource


class CommentAdmin(ImportExportModelAdmin):
    resource_class = CommentResource
    list_display = ('publish_date', 'text', 'sentiment')
    date_hierarchy = 'publish_date'


class SiteAdmin(admin.ModelAdmin):
    list_display = ('title', 'type')


admin.site.register(Site, SiteAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityLink)
admin.site.register(Theme)
admin.site.register(ThemeArticles)
admin.site.register(ThemeMarkup)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category)
admin.site.register(ArticleCategory)
admin.site.register(District)