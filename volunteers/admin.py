from django.contrib import admin

from volunteers.models import Edition
from volunteers.models import Track
from volunteers.models import Talk
from volunteers.models import TaskCategory
from volunteers.models import TaskTemplate
from volunteers.models import Task
from volunteers.models import Volunteer
from volunteers.models import VolunteerStatus
from volunteers.models import VolunteerTask
from volunteers.models import VolunteerCategory


class VolunteerTaskInline(admin.TabularInline):
    model = VolunteerTask
    extra = 1

class VolunteerCategoryInline(admin.TabularInline):
    model = VolunteerCategory
    extra = 1

class EditionAdmin(admin.ModelAdmin):
    fields = ['year', 'start_date', 'end_date']
    list_display = ['year', 'start_date', 'end_date']


class TrackAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['edition', 'date', 'start_time']}),
        (None, {'fields': ['title', 'description']}),
    ]
    list_display = ['edition', 'date', 'start_time', 'title']


class TalkAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['track', 'speaker', 'title']}),
        (None, {'fields': ['description']}),
        (None, {'fields': ['date', 'start_time', 'end_time']}),
    ]
    list_display = ['title', 'track', 'date', 'start_time']


class TaskCategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'description']
    inlines = (VolunteerCategoryInline, )
    list_display = ['name', 'assigned_volunteers']


class TaskTemplateAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'category']
    list_display = ['name', 'category']


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max', 'date', 'start_time', 'end_time']}),
        (None, {'fields': ['talk', 'template']}),
        (None, {'fields': ['description']}),
    ]
    inlines = (VolunteerTaskInline, )
    list_display = ['name', 'date', 'start_time', 'end_time', 'assigned_volunteers', 'nbr_volunteers']


class VolunteerAdmin(admin.ModelAdmin):
    fields = ['user', 'full_name', 'email', 'mobile_nbr']
    inlines = (VolunteerCategoryInline, VolunteerTaskInline)
    list_display = ['user', 'full_name', 'email', 'mobile_nbr']
    readonly_fields = ['full_name', 'email']


class VolunteerStatusAdmin(admin.ModelAdmin):
    fields = ['edition', 'volunteer', 'active']
    list_display = ['edition', 'volunteer', 'active']


admin.site.register(Edition, EditionAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(TaskCategory, TaskCategoryAdmin)
admin.site.register(TaskTemplate, TaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Volunteer, VolunteerAdmin)
admin.site.register(VolunteerStatus, VolunteerStatusAdmin)
