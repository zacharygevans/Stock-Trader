from os import name
from django.contrib import admin
from django.urls import path, include

import trader.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', trader.views.index, name='index'),
    path('sell/', trader.views.sell, name='sell'),
    path('reset/', trader.views.reset, name='reset'),
    path('accounts/', include('django.contrib.auth.urls')),
]
