from django.urls import path, re_path
from django.conf.urls.static import static
from django.views.static import serve as django_static_serve
import volunteers.views as views
from volunteers.views import *
from django.contrib import admin
from django.contrib.auth import views as auth_views
admin.autodiscover()

from volunteers.forms import ActivationAwareAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', promo, name='promo'),
    path('faq/', faq, name='faq'),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),
    path('privacy-consent/', privacy_policy_consent, name='privacy_policy_consent'),
    path('volunteers/signup', signup, name='signup'),

    re_path(
        r'^volunteers/(?P<username>(?!signout|signup|signin)[\.\w-]+)/$',
        profile_detail,
        name='userena_profile_detail'
    ),
    re_path(
        r'^volunteers/(?P<username>[\.\w-]+)/edit/$',
        profile_edit,
        name='userena_profile_edit'
    ),
    re_path(
        r'^volunteers/page/(?P<page>[0-9]+)/$',
        views.ProfileListView.as_view(),
        name='userena_profile_list_paginated'
    ),
    path('volunteers/', views.ProfileListView.as_view(), name='userena_profile_list'),

    re_path(r'^tasks/(?P<username>[\.\w-]+)', task_list_detailed, name='task_list_detailed'),
    path('task/<int:task_id>/', task_detailed, name='task_detailed'),
    path('talk/<int:talk_id>/', talk_detailed, name='talk_detailed'),
    path('tasks/', task_list, name='task_list'),
    path('event_sign_on/', event_sign_on, name='event_sign_on'),
    path('talks/', talk_list, name='talk_list'),
    path('category_schedule/', category_schedule_list, name='category_schedule_list'),
    path('task_schedule/<int:template_id>/', task_schedule, name='task_schedule'),
    path('task_schedule_csv/<int:template_id>/', task_schedule_csv, name='task_schedule_csv'),

    re_path(
        r'^media/(?P<path>.*)$',
        django_static_serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}
    ),
    path("accounts/login/", auth_views.LoginView.as_view(authentication_form=ActivationAwareAuthenticationForm), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/activate/<str:token>/", activate_account ,name="activate"),
    path('accounts/password/change/',
         auth_views.PasswordChangeView.as_view(template_name='userena/password_form.html'),
         name='userena_password_change'),
    path('accounts/password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='userena/password_reset_done.html'),
         name='userena_password_change_done'),
    path('accounts/email/change/', email_change,
         name='userena_email_change'),
]
