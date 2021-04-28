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

    # APPEALS
    path('appeals/', appeals.index, name='appeals'),

    # SOURCES
    path('sources/', sources.index, name='sources'),
    path('sources/add_source/', sources.add_source, name='add_source'),

    # PERSONS
    path('persons/', persons.index, name='persons'),
    path('persons/<int:ent_id>', persons.person_page, name='person_page'),

    # ORGS
    path('orgs/', orgs.index, name='orgs'),
    path('orgs/<int:ent_id>', orgs.org_page, name='org_page'),

    # ARTICLES
    path('items/', items.index, name='items'),

    # SEARCH
    path('search/', items.search, name='search'),

    # EVENTS
    path('events/', events.index, name='events'),
    path('events/<int:event_id>', events.info, name='event_info'),
    path('events/excel/<int:event_id>', events.excelview, name='event_excel'),
    path(
        'events/alt_title/',
        events.suggest_alt_title,
        name='event_alt_title'),

    # HAPPINESS
    path('happiness/', happiness.index, name='happiness'),
    path(
        'happiness_map/<int:category>/<str:start_date>/<str:end_date>/<str:map_type>',
        happiness.leaflet_map,
        name='leaflet_map'),
    path(
        'happiness/excel/<int:category>/<str:start_date>/<str:end_date>',
        happiness.excelview,
        name='happiness_excel'),
    path(
        'happiness/add',
        happiness.upload_custom_data,
        name='happiness_upload_custom_data'),
    path(
        'happiness/example_df.csv',
        happiness.example_csv,
        name='happiness_example_csv'),

    # AUTH
    path('accounts/', include('django.contrib.auth.urls')),
]

# AUTH
# accounts/ login/ [name='login']
# accounts/ logout/ [name='logout']
# accounts/ password_change/ [name='password_change']
# accounts/ password_change/done/ [name='password_change_done']
# accounts/ password_reset/ [name='password_reset']
# accounts/ password_reset/done/ [name='password_reset_done']
# accounts/ reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/ reset/done/ [name='password_reset_complete']
