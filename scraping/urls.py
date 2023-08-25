# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from . import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('scrape', views.scrape, name='scrape'),
    path('run_cron', views.run_cron, name='run_cron'),
    path('getRecordsFromPhoneBurner', views.getRecordsFromPhoneBurner, name='getRecordsFromPhoneBurner'),
]
