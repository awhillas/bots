from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from dh5bp.urls import urlpatterns as dh5bp_urls
handler404 = 'dh5bp.views.page_not_found'
handler500 = 'dh5bp.views.server_error'

from orders.views import *

urlpatterns = patterns('',
	url(r'^$', HomeView.as_view(), name='home'),
	url(r'^bake/', include('orders.urls')),
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
)
urlpatterns += dh5bp_urls