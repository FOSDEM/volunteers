from django.conf.urls import patterns, url
from volunteers import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='volunteer_index'),
    url(r'^(?P<volunteer_id>\d+)/$', views.volunteer_detail, name='volunteer_detail'),
    url(r'^(?P<volunteer_id>\d+)/edit/$', views.volunteer_edit, name='volunteer_edit'),
)
