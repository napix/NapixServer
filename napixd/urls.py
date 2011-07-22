from django.conf.urls.defaults import patterns, include, url
from napixd.handlers import NAPIXHandler

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = NAPIXHandler.get_urls()

