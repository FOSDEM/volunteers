from django.contrib import admin
from django.db.models import get_models, get_app
from django.contrib.admin.sites import AlreadyRegistered
from volunteers.models import *
import sys
import inspect



app_models = get_app('volunteers')

for model in get_models(app_models):
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
