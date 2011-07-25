from django.conf.urls.defaults import patterns, include, url
from napixd.views import get_urls

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = get_urls()

