from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

# Create your models here.

class Edition(models.Model):
    class Meta:
        verbose_name = _('Edition')
        verbose_name_plural = _('Editions')

    def __unicode__(self):
        return self.year

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

    def __unicode__(self):
        return self.title

    title = models.CharField(max_length=128)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()


class Talk(models.Model):
    class Meta:
        verbose_name = _('Talk')
        verbose_name_plural = _('Talks')

    def __unicode__(self):
        return self.title

    track = models.ForeignKey(Track)
    title = models.CharField(max_length=128)
    speaker = models.CharField(max_length=50)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()


"""
Categories are things like buildup, cleanup, moderation, ...
"""
class TaskCategory(models.Model):
    class Meta:
        verbose_name = _('Task Category')
        verbose_name_plural = _('Task Categories')

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    volunteers = models.ManyToManyField('Volunteer')

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

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory)


"""
Contains the specifics of an instance of a task. It's based on a task template
but it can override the name and description, yet not the category.
"""
class Task(models.Model):
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    nbr_volunteers = models.IntegerField()
    # Only for moderation, or possible future tasks related
    # to a specific talk.
    talk = models.ForeignKey(Talk, blank=True, null=True)
    template = models.ForeignKey(TaskTemplate)
    volunteers = models.ManyToManyField('Volunteer')


"""
The nice guys n' gals who make it all happen.
"""
class Volunteer(models.Model):
    class Meta:
        verbose_name = _('Volunteer')
        verbose_name_plural = _('Volunteers')

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=50)
    email = models.EmailField()
    user = models.ForeignKey(User)
    # Categories in which they're interested to help out.
    categories = models.ManyToManyField(TaskCategory)
    # Tasks for which they've signed up.
    tasks = models.ManyToManyField(Task)


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
        return '%s - %s: %s' % (self.volunteer.name,
            self.edition.year,
            'Yes' if self.active else 'No')

    active = models.BooleanField()
    volunteer = models.ForeignKey(Volunteer)
    edition = models.ForeignKey(Edition)
