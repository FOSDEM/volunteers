from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'volunteer_mgmt.views.home', name='home'),
    # url(r'^volunteer_mgmt/', include('volunteer_mgmt.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^volunteers/', include('volunteers.urls', namespace='volunteers')),
    url(r'^accounts/login/.*$', 'django.contrib.auth.views.login'),
    url(r'^volunteers/LogOut/$', 'volunteers.views.logOut'),
    #url(r'^AddTasks/$', views.add_tasks, name='add_tasks'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
