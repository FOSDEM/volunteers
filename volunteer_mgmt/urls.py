from django.conf.urls import include, url
from django.urls import path
from django.conf.urls.static import static
from django.views.static import serve as django_static_serve
import volunteers.views as views
from volunteers.views import *
from django.contrib import admin
from django.contrib.auth import views as auth_views
admin.autodiscover()


urlpatterns = [
    # Examples:
    # url(r'^$', 'volunteer_mgmt.views.home', name='home'),
    # url(r'^volunteer_mgmt/', include('volunteer_mgmt.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    # Userena urls:
    url(r'^$', promo, name='promo'),
    url(r'^faq/', faq, name='faq'),
    url(r'^privacy_policy/', privacy_policy, name='privacy_policy'),
    url(r'^privacy-consent/', privacy_policy_consent, name='privacy_policy_consent'),
    url(r'^volunteers/signup', signup, name='signup'),
    url(r'^volunteers/(?P<username>(?!signout|signup|signin)[\.\w-]+)/$', profile_detail, name='userena_profile_detail'),
    url(r'^volunteers/(?P<username>[\.\w-]+)/edit/$', profile_edit, name='userena_profile_edit'),
    url(r'^volunteers/page/(?P<page>[0-9]+)/$', views.ProfileListView.as_view(), name='userena_profile_list_paginated'),
    url(r'^volunteers/$', views.ProfileListView.as_view(), name='userena_profile_list'),
    #url(r'^volunteers/signin/$', views.ProfileListView.as_view(), name='userena_signin'),
    #url(r'^volunteers/', include('userena.urls')),
    #url(r'^messages/', include('userena.contrib.umessages.urls')),
    # other urls:
    url(r'^tasks/(?P<username>[\.\w-]+)', task_list_detailed, name='task_list_detailed'),
    url(r'^task/(?P<task_id>\d+)/$', task_detailed, name='task_detailed'),
    url(r'^talk/(?P<talk_id>\d+)/$', talk_detailed, name='talk_detailed'),
    url(r'^tasks/', task_list, name='task_list'),
    url(r'^event_sign_on/', event_sign_on, name='event_sign_on'),
    url(r'^talks/', talk_list, name='talk_list'),
    url(r'^category_schedule/', category_schedule_list, name='category_schedule_list'),
    url(r'^task_schedule/(?P<template_id>\d+)/$', task_schedule, name='task_schedule'),
    url(r'^task_schedule_csv/(?P<template_id>\d+)/$', task_schedule_csv, name='task_schedule_csv'),
    url(r'^media/(?P<path>.*)$', django_static_serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('accounts/password/change/',
         auth_views.PasswordChangeView.as_view(template_name='userena/password_form.html'),
         name='userena_password_change'),
    path('accounts/password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='userena/password_reset_done.html'),
         name='userena_password_change_done'),
    path('accounts/email/change/', email_change,
         name='userena_email_change'),
]
