from django.db import models
from django.contrib.auth.models import User
from userena.models import UserenaLanguageBaseProfile
from django.utils.translation import ugettext_lazy as _
import datetime
import time
from dateutil.relativedelta import relativedelta

# Helper model
class HasLinkField():
    def link(self):
        return 'Link'


# Create your models here.

class Edition(models.Model):
    class Meta:
        verbose_name = _('Edition')
        verbose_name_plural = _('Editions')
        ordering = ['-year']

    def __unicode__(self):
        return unicode(self.year)

    @classmethod
    def get_current_year(self):
        return (datetime.date.today() + relativedelta(months=+6)).year

    @classmethod
    def get_current(self):
        retval = False
        current = self.objects.filter(year=self.get_current_year())
        if current:
            retval = current[0].id
        return retval

    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()


"""
A track is a collection of talks, grouped around one single
concept or subject.
"""
class Track(models.Model):
    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')
        ordering = ['date','start_time','title']

    def __unicode__(self):
        return self.title

    title = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    edition = models.ForeignKey(Edition, default=Edition.get_current)
    date = models.DateField(default=datetime.date(2014,2,1))
    start_time = models.TimeField()
    # end_time = models.TimeField()


class Talk(models.Model, HasLinkField):
    class Meta:
        verbose_name = _('Talk')
        verbose_name_plural = _('Talks')
        ordering = ['date','start_time','-end_time','title']

    def __unicode__(self):
        return self.title

    track = models.ForeignKey(Track)
    title = models.CharField(max_length=256)
    speaker = models.CharField(max_length=128)
    description = models.TextField()
    date = models.DateField(default=datetime.date(2014,2,1))
    start_time = models.TimeField()
    end_time = models.TimeField()
    volunteers = models.ManyToManyField('Volunteer', through='VolunteerTalk', blank=True, null=True)

    def assigned_volunteers(self):
        return self.volunteers.count()


"""
Categories are things like buildup, cleanup, moderation, ...
"""
class TaskCategory(models.Model):
    class Meta:
        verbose_name = _('Task Category')
        verbose_name_plural = _('Task Categories')
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    volunteers = models.ManyToManyField('Volunteer', through='VolunteerCategory', blank=True, null=True)

    def assigned_volunteers(self):
        return self.volunteer_set.count()


"""
A task template contains all the data about a task that isn't task specific.
For example, cleanup can happen in multiple locations or at multiple times.
Not sure we need this, but it seemed like a good thing to have when I wrote
down the DB model. ;)
"""
class TaskTemplate(models.Model):
    class Meta:
        verbose_name = _('Task Template')
        verbose_name_plural = _('Task Templates')
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory)


"""
Contains the specifics of an instance of a task. It's based on a task template
but it can override the name and description, yet not the category.
"""
class Task(models.Model, HasLinkField):
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['date','start_time','-end_time','name']

    def __unicode__(self):
        day = self.date.strftime('%a')
        start = self.start_time.strftime('%H:%M')
        end = self.end_time.strftime('%H:%M')
        return "%s (%s, %s - %s)" % (self.name, day, start, end)

    name = models.CharField(max_length=300)
    description = models.TextField()
    date = models.DateField(default=datetime.date(2014,2,1))
    start_time = models.TimeField()
    end_time = models.TimeField()
    nbr_volunteers = models.IntegerField(default=0)
    nbr_volunteers_min = models.IntegerField(default=0)
    nbr_volunteers_max = models.IntegerField(default=0)
    # Only for moderation, or possible future tasks related
    # to a specific talk.
    talk = models.ForeignKey(Talk, blank=True, null=True)
    template = models.ForeignKey(TaskTemplate)
    volunteers = models.ManyToManyField('Volunteer', through='VolunteerTask', blank=True, null=True)

    def assigned_volunteers(self):
        return self.volunteer_set.count()


"""
table to contain the language names and ISO codes
"""
class Language(models.Model):
    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=128)
    iso_code = models.CharField(max_length=2)


"""
The nice guys n' gals who make it all happen.
"""
class Volunteer(UserenaLanguageBaseProfile):
    class Meta:
        verbose_name = _('Volunteer')
        verbose_name_plural = _('Volunteers')
        ordering = ['user__first_name', 'user__last_name']

    def __unicode__(self):
        return self.user.username

    ratings = (
        (0, 'No longer welcome'),
        (1, 'Poor'),
        (2, 'Not great'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Superb'),
    )

    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='volunteer')
    # Categories in which they're interested to help out.
    categories = models.ManyToManyField(TaskCategory, through='VolunteerCategory', blank=True, null=True, \
        help_text="""<br/><br/>
        Indicate your preference for which kind of tasks you'd prefer to do.
        The tasks belonging to this category will appear on top in the Tasks page, so you
        can find them easily.<br/><br/>
        Signing up for actual tasks does not happen here; that's done in the Tasks screen!""")
    # Tasks for which they've signed up.
    tasks = models.ManyToManyField(Task, through='VolunteerTask', blank=True, null=True)
    editions = models.ManyToManyField(Edition, through='VolunteerStatus', blank=True, null=True)
    signed_up = models.DateField(default=datetime.date.today)
    about_me = models.TextField(_('about me'), blank=True)
    mobile_nbr = models.CharField('Mobile Phone', max_length=30, blank=True, null=True, \
        help_text="We won't share this, but we need it in case we need to contact you in a pinch during the event.")
    private_staff_rating = models.IntegerField(null=True, blank=True, choices=ratings)
    private_staff_notes = models.TextField(null=True, blank=True)

    # Just here for the admin interface.
    def full_name(self):
        return " ".join([self.user.first_name, self.user.last_name])

    def email(self):
        return self.user.email

    # Dr. Manhattan detection: is this person capable of being in multiple places at once?
    def detect_dr_manhattan(self):
        retval = [False, []]
        current_tasks = self.tasks.filter(date__year=Edition.get_current_year())
        dates = [x.date for x in current_tasks.order_by('date').distinct('date')]
        # Yes yes, I know about dict generators; my editor doesn't however and I don't
        # want to see warnings for perfectly valid code.
        schedule = {}
        for date in dates:
            schedule[date] = []
        for task in current_tasks:
            for item in schedule[task.date]:
                if item.start_time <= task.start_time < item.end_time \
                    or item.start_time < task.end_time <= item.end_time:
                    retval[0] = True
                    item_found = False
                    for task_set in retval[1]:
                        if item in task_set:
                            item_found = True
                            task_set.add(task)
                            break
                    if not item_found:
                        retval[1].append(set([item, task]))
            schedule[task.date].append(task)
        return retval


"""
Many volunteers come back year after year, but sometimes they
take a hiatus of one or multiple years. This is there to capture
their availability on a per-event basis, in order to filter out
inactive volunteers from the selection pool.
"""
class VolunteerStatus(models.Model):
    class Meta:
        verbose_name = _('Volunteer Status')
        verbose_name_plural = _('Volunteer Statuses')

    def __unicode__(self):
        return '%s %s - %s: %s' % (self.volunteer.user.first_name,
            self.volunteer.user.last_name, self.edition.year,
            'Yes' if self.active else 'No')

    active = models.BooleanField()
    volunteer = models.ForeignKey(Volunteer)
    edition = models.ForeignKey(Edition, default=Edition.get_current)


"""
M2M tables because I want to have the relationship on both model admin pages
"""
class VolunteerTask(models.Model):
    class Meta:
        verbose_name = _('VolunteerTask')
        verbose_name_plural = _('VolunteerTasks')

    def __unicode__(self):
        return self.task

    volunteer = models.ForeignKey(Volunteer)
    task = models.ForeignKey(Task)


class VolunteerCategory(models.Model):
    class Meta:
        verbose_name = _('VolunteerCategory')
        verbose_name_plural = _('VolunteerCategories')

    def __unicode__(self):
        return self.category

    volunteer = models.ForeignKey(Volunteer)
    category = models.ForeignKey(TaskCategory)


"""
link table between volunteers and languages
"""
class VolunteerLanguage(models.Model):
    class Meta:
        verbose_name = _('VolunteerLanguage')
        verbose_name_plural = _('VolunteerLanguages')

    def __unicode__(self):
        return self.language

    volunteer = models.ForeignKey(Volunteer)
    language = models.ForeignKey(Language)


"""
link table between volunteers and talks
"""
class VolunteerTalk(models.Model):
    class Meta:
        verbose_name = _('VolunteerTalk')
        verbose_name_plural = _('VolunteerTalks')

    def __unicode__(self):
        return self.talk

    volunteer = models.ForeignKey(Volunteer)
    talk = models.ForeignKey(Talk)
