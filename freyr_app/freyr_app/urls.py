"""freyr_app URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

from core.views import (
    index,
    sources,
    persons,
    orgs,
    items,
    events,
    happiness,
    appeals
)

urlpatterns = [
    # ADMIN
    path('admin/', admin.site.urls, name='admin'),
    # ENTER
    path('', index.index, name='index'),
    # BASE PATHS
    path('appeals/', appeals.index, name='appeals'),
    path('sources/', sources.index, name='sources'),
    path('sources/add_source/', sources.add_source, name='add_source'),
    path('persons/', persons.index, name='persons'),
    path('persons/<int:ent_id>', persons.person_page, name='person_page'),
    path('orgs/', orgs.index, name='orgs'),
    path('orgs/<int:ent_id>', orgs.org_page, name='org_page'),
    path('items/', items.index, name='items'),
    path('events/', events.index, name='events'),
    path('events/<int:event_id>', events.info, name='event_info'),
    path('events/excel/<int:event_id>', events.excelview, name='event_excel'),
    path('events/alt_title/', events.suggest_alt_title, name='event_alt_title'),
    path('happiness/', happiness.index, name='happiness'),
    path('happiness_map/<int:category>/<str:start_date>/<str:end_date>', happiness.leaflet_map, name='leaflet_map'),
    path('happiness/excel/<int:category>/<str:start_date>/<str:end_date>', happiness.excelview, name='happiness_excel'),
    # AUTH
    path('accounts/', include('django.contrib.auth.urls')),
]
