import sys
from django.contrib import admin
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mass_mail
from django.db import models
from django.db.models import Count
from django.forms import TextInput, Textarea, Form, CharField, MultipleHiddenInput
from django.http import HttpResponse, HttpResponseRedirect
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

import datetime

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
            return queryset.filter(date__week_day=self.value())
        else:
            return queryset

class NumTasksFilter(admin.SimpleListFilter):
    title = 'tasks'
    parameter_name = 'tasks'

    def lookups(self, request, model_admin):
        return (
            (0, 'No tasks'),
            (1, '1 - 5 tasks'),
            (2, 'More than 5 tasks'),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        val = int(self.value())
        if val == 0:
            min_tasks, max_tasks = (0, 0)
        elif val == 1:
            min_tasks, max_tasks = (1, 5)
        else:
            min_tasks, max_tasks = (6, sys.maxint)
        return queryset.annotate(num_tasks=Count('tasks')). \
            filter(num_tasks__gte=min_tasks, num_tasks__lte=max_tasks)


class EditionFilter(admin.SimpleListFilter):
    title = 'editions'
    parameter_name = 'edition'

    def lookups(self, request, model_admin):
        retval = [(0, 'All')]
        for edition in Edition.objects.all():
            retval.append((edition.id, edition.name))
        return retval

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = Edition.get_current()
        else:
            # Otherwise, the selected value doesn't get highlighted for some reason...
            # Note: there is something very weird about this. self.value() should
            # return, and operate on, unicode strings, even for "integers".
            # Compare to DayListFilter above...
            # TODO: Investigate.
            self.used_parameters[self.parameter_name] = int(self.value())
        if self.value() == 0:
            return queryset
        elif 'edition' in queryset.model.__dict__:
            return queryset.filter(edition=self.value())
        elif 'track' in queryset.model.__dict__:
            return queryset.filter(track__edition=self.value())
        elif 'volunteerstatus_set' in queryset.model.__dict__:
            return queryset.filter(volunteerstatus__edition=self.value())

class SignupFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'singup edition'
    parameter_name = 'singup'

    def lookups(self, request, model_admin):
        retval = set()
        editions = Edition.objects.all().order_by('start_date')
        for val in [(e.id, e.name) for e in editions]:
            retval.add(val)
        return retval

    def queryset(self, request, queryset):
        if self.value():
            edition = Edition.objects.get(pk=self.value())
            return queryset.filter(signed_up__gte=edition.visible_from, signed_up__lte=edition.visible_until)
        else:
            return queryset

class CategoryActiveFilter(admin.SimpleListFilter):
    title = 'active category'
    parameter_name = 'active'

    def lookups(self, requesst, model_admin):
        return [
            (2, 'All'),
            (1, 'Yes'),
            (0, 'No'),
        ]

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = 1
        else:
            self.used_parameters[self.parameter_name] = int(self.value())
        if self.value() == 2:
            return queryset
        return queryset.filter(category__active=self.value())


class VolunteerTaskInline(admin.TabularInline):
    model = VolunteerTask
    extra = 1

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(VolunteerTaskInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'task':
            field.queryset = field.queryset.order_by('-edition__start_date', 'name')
        return field


class VolunteerCategoryInline(admin.TabularInline):
    model = VolunteerCategory
    extra = 1


class EditionAdmin(admin.ModelAdmin):
    fields = ['name', 'start_date', 'end_date', 'visible_from', 'visible_until']
    list_display = ['name', 'start_date', 'end_date', 'visible_from', 'visible_until']


class TrackAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['edition', 'date', 'start_time']}),
        (None, {'fields': ['title', 'description']}),
    ]
    list_display = ['edition', 'date', 'start_time', 'title']
    list_filter = [EditionFilter]



class TalkAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['track', 'speaker', 'title']}),
        (None, {'fields': ['description']}),
        (None, {'fields': ['date', 'start_time', 'end_time']}),
    ]
    list_display = ['link', 'title', 'track', 'date', 'start_time']
    list_editable = ['title', 'track', 'date', 'start_time']
    list_filter = [EditionFilter, DayListFilter, 'track']


class TaskCategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'description']
    inlines = (VolunteerCategoryInline, )
    list_display = ['link', 'name', 'assigned_volunteers', 'active']
    list_editable = ['name', 'active']


class TaskTemplateAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'category']
    list_display = ['name', 'category']
    list_filter = [CategoryActiveFilter]


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['edition', 'name', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max', 'date', 'start_time', 'end_time']}),
        (None, {'fields': ['talk', 'template']}),
        (None, {'fields': ['description']}),
    ]
    inlines = (VolunteerTaskInline, )
    list_display = ['link', 'edition', 'name', 'date', 'start_time', 'end_time', 'assigned_volunteers', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max']
    list_editable = ['name', 'date', 'start_time', 'end_time', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max']
    list_filter = [EditionFilter, DayListFilter, 'template', 'talk__track']


class VolunteerAdmin(admin.ModelAdmin):
    fields = ['user', 'full_name', 'email', 'mobile_nbr', 'private_staff_rating', 'private_staff_notes']
    inlines = (VolunteerCategoryInline, VolunteerTaskInline)
    list_display = ['user', 'full_name', 'email', 'private_staff_rating', 'private_staff_notes', 'mobile_nbr', 'num_tasks']
    list_editable = ['private_staff_rating', 'private_staff_notes', 'mobile_nbr']
    list_filter = [EditionFilter, SignupFilter, 'private_staff_rating', NumTasksFilter, 'categories', 'tasks']
    readonly_fields = ['full_name', 'email']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':20})},
    }
    actions = ['mass_mail_volunteer', 'vcard_export']


    # Mass mail action
    class MassMailForm(Form):

        _selected_action = CharField(widget=MultipleHiddenInput)
        subject = CharField()
        message = CharField(widget=Textarea)

    def mass_mail_volunteer(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
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

    # vCard export
    def vcard_export(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        output = ''
        for volunteer in queryset:
            output += volunteer.vcard()
        response = HttpResponse(output, mimetype='text/vcard')
        response['Content-Disposition'] = 'attachment; filename=volunteers.vcard'
        return response

    def num_tasks(self, volunteer):
        return volunteer.tasks.filter(edition=Edition.get_current).count()

    num_tasks.admin_order_field = 'num_tasks'

class VolunteerStatusAdmin(admin.ModelAdmin):
    fields = ['edition', 'volunteer', 'active']
    list_display = ['edition', 'volunteer', 'active']
    list_filter = [EditionFilter]


admin.site.register(Edition, EditionAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(TaskCategory, TaskCategoryAdmin)
admin.site.register(TaskTemplate, TaskTemplateAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Volunteer, VolunteerAdmin)
admin.site.register(VolunteerStatus, VolunteerStatusAdmin)
