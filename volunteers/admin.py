from django.contrib import admin
from django.conf import settings
from django.core.mail import send_mass_mail
from django.db import models
from django.forms import TextInput, Textarea, Form, CharField, MultipleHiddenInput
from django.http import HttpResponseRedirect
from django.shortcuts import render

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


class DayListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'day'
    parameter_name = 'day'

    def lookups(self, request, model_admin):
        return (
            (6, 'Friday'),
            (7, 'Saturday'),
            (1, 'Sunday'),
            (2, 'Monday'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(date__year=Edition.get_current_year(), \
                date__week_day=self.value())
        else:
            return queryset


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
    list_display = ['link', 'title', 'track', 'date', 'start_time']
    list_editable = ['title', 'track', 'date', 'start_time']
    list_filter = [DayListFilter, 'track']


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
    list_display = ['link', 'name', 'date', 'start_time', 'end_time', 'assigned_volunteers', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max']
    list_editable = ['name', 'date', 'start_time', 'end_time', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max']
    list_filter = [DayListFilter, 'template', 'talk__track']


class VolunteerAdmin(admin.ModelAdmin):
    fields = ['user', 'full_name', 'email', 'mobile_nbr', 'private_staff_rating', 'private_staff_notes']
    inlines = (VolunteerCategoryInline, VolunteerTaskInline)
    list_display = ['user', 'full_name', 'email', 'private_staff_rating', 'private_staff_notes', 'mobile_nbr']
    list_editable = ['private_staff_rating', 'private_staff_notes', 'mobile_nbr']
    list_filter = ['private_staff_rating']
    readonly_fields = ['full_name', 'email']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }
    actions = ['mass_mail_volunteer']


    # Mass mail action
    class MassMailForm(Form):

        _selected_action = CharField(widget=MultipleHiddenInput)
        subject = CharField()
        message = CharField(widget=Textarea)

    def mass_mail_volunteer(self, request, queryset):
        form = None
        if 'send' in request.POST:
            form = self.MassMailForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                count = 0
                plural = ''
                volunteer_mails = []
                for volunteer in queryset:
                    # TODO: actually send the mail
                    if volunteer.user.email:
                        volunteer_mails.append(volunteer.user.email)
                        count += 1
                send_mass_mail(((subject, message, settings.DEFAULT_FROM_EMAIL, volunteer_mails),), fail_silently=False)
                if count > 1:
                    plural = 's'
                self.message_user(request, 'Mail with subject "%s" sent to  %d volunteer%s.' % (subject, count, plural))
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.MassMailForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            return render(request, 'admin/massmail.html', {'volunteers': queryset,
                                                             'massmail_form': form,
                                                            })
    mass_mail_volunteer.short_description = "Send mass mail"


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
