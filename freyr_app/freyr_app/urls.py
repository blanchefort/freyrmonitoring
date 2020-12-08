"""freyr_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from core.views import index, sources, persons, orgs, items, events

urlpatterns = [
    # ADMIN
    path('admin/', admin.site.urls, name='admin'),
    # ENTER
    path('', index.index, name='index'),
    # BASE PATHS
    path('sources/', sources.index, name='sources'),
    path('sources/add_source/', sources.add_source, name='add_source'),
    path('persons/', persons.index, name='persons'),
    path('persons/<int:ent_id>', persons.person_page, name='person_page'),
    path('orgs/', orgs.index, name='orgs'),
    path('orgs/<int:ent_id>', orgs.org_page, name='org_page'),
    path('items/', items.index, name='items'),
    path('events/', events.index, name='events'),
    path('events/<int:event_id>', events.info, name='event_info'),
    # AUTH
    path('accounts/', include('django.contrib.auth.urls')),
]
