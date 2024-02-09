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
    title = 'number of tasks'
    parameter_name = 'number_of_tasks'

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
            min_tasks, max_tasks = (6, sys.maxsize)
        return queryset.annotate(num_tasks=Count('tasks')). \
            filter(num_tasks__gte=min_tasks, num_tasks__lte=max_tasks)


class TaskCategoryFilter(admin.SimpleListFilter):
    title = '{0} categories'.format(Edition.get_current().name) if Edition.get_current() else None
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        templates = []
        for template in TaskTemplate.objects.all():
            templates.append((template.id, template.name))
        return templates

    def queryset(self, request, queryset):
        if not self.value() or self.value() == 0:
            return queryset
        return Volunteer.objects.filter(
            tasks__edition_id=Edition.get_current(),
            tasks__template_id=self.value()
        ).distinct()


class TaskFilter(admin.SimpleListFilter):
    title = '{0} tasks'.format(Edition.get_current().name) if Edition.get_current() else None
    parameter_name = 'task'

    def lookups(self, request, model_admin):
        tasks = []
        for task in Task.objects.filter(edition=Edition.get_current()).order_by('date', 'name', 'start_time'):
            day = task.date.strftime('%a')
            start = task.start_time.strftime('%H:%M')
            end = task.end_time.strftime('%H:%M')
            name = '{0} ({1} {2} - {3})'.format(task.name, day, start, end)
            tasks.append((task.id, name))
        return tasks

    def queryset(self, request, queryset):
        if not self.value() or self.value() == 0:
            return queryset
        return Volunteer.objects.filter(tasks__id=self.value()).distinct()


class MyVolunteersFilter(admin.SimpleListFilter):
    title = 'tasks I\'m primary on'
    parameter_name = 'my_task'

    def lookups(self, request, model_admin):
        tasks = []
        for task_template in TaskTemplate.objects.filter(primary__id=int(request.user.id)):
            tasks.append((task_template.id, task_template.name))
        return tasks

    def queryset(self, request, queryset):
        if not self.value() or self.value() == 0:
            return queryset
        return Volunteer.objects.filter(
            tasks__template__id=self.value(),
            tasks__edition_id=Edition.get_current()
        ).distinct()


class ThisYearsVolunteersFilter(admin.SimpleListFilter):
    title = 'volunteers for this edition'
    parameter_name = 'this_edition'

    def lookups(self, request, model_admin):
        edition = Edition.get_current()
        return [(edition.id, edition.name)]

    def queryset(self, request, queryset):
        if not self.value() or self.value() == 0:
            return queryset
        return Volunteer.objects.filter(
            tasks__edition_id=Edition.get_current()
        ).distinct()


class LastYearVolunteersNoTaskFilter(admin.SimpleListFilter):
    title = 'last year volunteers without tasks'
    parameter_name = 'volunteers_no_task'

    def lookups(self, request, model_admin):
        edition = Edition.get_previous()
        return [
            (edition.id, edition.name)
        ]

    def queryset(self, request, queryset):
        if not self.value() or self.value() == 0:
            return queryset
        return Volunteer.objects.filter(
            tasks__edition=Edition.get_previous()
        ).exclude(
            tasks__edition=Edition.get_current()
        ).distinct()


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


class EditionAdmin(admin.ModelAdmin):
    fields = ['name', 'start_date', 'end_date', 'visible_from', 'visible_until', 'digital_edition']
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
        (None, {'fields': ['description', 'fosdem_url']}),
        (None, {'fields': ['date', 'start_time', 'end_time']}),
    ]
    list_display = ['link', 'title', 'track', 'date', 'start_time']
    list_editable = ['title', 'track', 'date', 'start_time']
    list_filter = [EditionFilter, DayListFilter, 'track']


class TaskCategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'description']
#    inlines = (VolunteerCategoryInline,)
    list_display = ['link', 'name', 'active']
    list_editable = ['name', 'active']


class TaskTemplateAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'category', 'primary']
    list_display = ['link', 'name', 'category', 'primary']
    list_editable = ['name', 'category', 'primary']
    list_filter = [CategoryActiveFilter]


class VolunteerTaskAdmin(admin.ModelAdmin):
    fields = ['volunteer', 'task']
    #list_display = ['volunteer__user', 'task__name']


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['edition', 'name', 'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max', 'date',
                           'start_time', 'end_time', 'location']}),
        (None, {'fields': ['talk', 'template']}),
        (None, {'fields': ['description', 'fosdem_url']}),
    ]
#    inlines = (VolunteerTaskInline,)
    list_display = ['link', 'edition', 'name', 'date', 'start_time', 'end_time', 'assigned_volunteers',
                    'nbr_volunteers', 'nbr_volunteers_min', 'nbr_volunteers_max', 'location']
    list_editable = ['name', 'date', 'start_time', 'end_time', 'nbr_volunteers', 'nbr_volunteers_min',
                     'nbr_volunteers_max', 'location']
    list_filter = [EditionFilter, DayListFilter, 'template', 'talk__track']

    actions = ['mass_mail_volunteer']

    # Mass mail action
    class MassMailForm(Form):

        _selected_action = CharField(widget=MultipleHiddenInput)
        subject = CharField()
        message = CharField(widget=Textarea)
    def mass_mail_volunteer(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        form = None

        volunteers = Volunteer.objects.filter(task__in=queryset).distinct()

        if 'send' in request.POST:
            form = self.MassMailForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                count = 0
                plural = ''
                for volunteer in volunteers:
                    if volunteer.user.email:
                        # Would have preferred to collect the mails in volunteer_mails list,
                        # then send one mail outside this loop, but we don't want volunteers
                        # to see each other's email addresses for privacy reasons, which means
                        # BCC, which means it will get sent out as separate mails anyway.
                        send_mass_mail(((subject, message, settings.DEFAULT_FROM_EMAIL, [volunteer.user.email]),),
                                       fail_silently=False)
                        count += 1
                if count > 1:
                    plural = 's'
                self.message_user(request,
                                  'Mail with subject "{}" sent to  {} volunteer{}.'.format(subject, count, plural))
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.MassMailForm(initial={'_selected_action': request.POST.getlist("_selected_action")})
            return render(request, 'admin/massmail.html', {'volunteers': volunteers,
                                                           'massmail_form': form,
                                                           })

    mass_mail_volunteer.short_description = "Send mass mail"


class VolunteerAdmin(admin.ModelAdmin):
    fields = ['user', 'full_name', 'email', 'mobile_nbr', 'private_staff_rating', 'private_staff_notes',
              'penta_account_name']
#    inlines = (VolunteerCategoryInline, VolunteerTaskInline)
    list_display = ['full_name', 'mobile_nbr', 'matrix_id', 'email', 'private_staff_rating', 'private_staff_notes']
    list_editable = ['private_staff_rating', 'private_staff_notes', 'mobile_nbr']
    list_filter = [MyVolunteersFilter, TaskCategoryFilter, ThisYearsVolunteersFilter,
                   TaskFilter, 'private_staff_rating']
    readonly_fields = ['full_name', 'email']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})},
    }
    actions = ['mass_mail_volunteer', 'mail_schedule']

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
                for volunteer in queryset:
                    if volunteer.user.email:
                        # Would have preferred to collect the mails in volunteer_mails list,
                        # then send one mail outside this loop, but we don't want volunteers
                        # to see each other's email addresses for privacy reasons, which means
                        # BCC, which means it will get sent out as separate mails anyway.
                        send_mass_mail(((subject, message, settings.DEFAULT_FROM_EMAIL, [volunteer.user.email]),),
                                       fail_silently=False)
                        count += 1
                if count > 1:
                    plural = 's'
                self.message_user(request,
                                  'Mail with subject "{}" sent to  {} volunteer{}.'.format(subject, count, plural))
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.MassMailForm(initial={'_selected_action': request.POST.getlist("_selected_action")})
            return render(request, 'admin/massmail.html', {'volunteers': queryset,
                                                           'massmail_form': form,
                                                           })

    mass_mail_volunteer.short_description = "Send mass mail"

    def mail_schedule(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        for volunteer in queryset:
            volunteer.mail_schedule()
        count = len(queryset)
        plural = 's' if count > 1 else ''
        self.message_user(request, 'Volunteer schedule sent to  {} volunteer{}.'.format(count, plural))
        return HttpResponseRedirect(request.get_full_path())

    def num_tasks(self, volunteer):
        return volunteer.tasks.filter(edition=Edition.get_current()).count()

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
admin.site.register(VolunteerTask, VolunteerTaskAdmin)
