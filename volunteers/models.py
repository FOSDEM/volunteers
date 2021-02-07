import datetime
# from dateutil import relativedelta
import hashlib
import http.client
import os
import urllib.request, urllib.parse, urllib.error
import vobject
import xml.etree.ElementTree as ET
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import ugettext_lazy as _
from userena.models import UserenaLanguageBaseProfile
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import connections
from django.db.models import PROTECT, CASCADE

# Parse dates, times, DRY
def parse_datetime(date_str, format='%Y-%m-%d'):
    return datetime.datetime.strptime(date_str, format)


def parse_date(date_str, format='%Y-%m-%d'):
    return parse_datetime(date_str, format).date()


def parse_time(date_str, format='%H:%M'):
    return parse_datetime(date_str, format).time()


# More DRY: given a start hour and duration, return start and end time.
def parse_hour_duration(start_str, duration_str, format='%H:%M'):
    start = datetime.datetime.strptime(start_str, format)
    dur_tm = datetime.datetime.strptime(duration_str, format)
    duration = datetime.timedelta(hours=dur_tm.hour, minutes=dur_tm.minute, seconds=dur_tm.second)
    end = start + duration
    start_tm = datetime.time(hour=start.hour, minute=start.minute, second=start.second)
    end_tm = datetime.time(hour=end.hour, minute=end.minute, second=end.second)
    return (start_tm, end_tm)


# Helper model
# class HasLinkField():
#    def link(self):
#        return 'Link'


# Create your models here.

class Edition(models.Model):
    class Meta:
        verbose_name = _('Edition')
        verbose_name_plural = _('Editions')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    name = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    visible_from = models.DateField()
    visible_until = models.DateField()
    digital_edition = models.BooleanField(default=False)

    @classmethod
    def get_current(cls):
        retval = False
        today = datetime.date.today()
        try:
            current = cls.objects.filter(visible_from__lte=today, visible_until__gte=today)
            if current:
                retval = current[0]
        except:
            return False
        return retval

    @classmethod
    def get_previous(cls):
        today = datetime.date.today()
        previous = cls.objects.filter(end_date__lt=today)
        if previous:
            return previous[0]
        return False

    @classmethod
    def penta_create_or_update(cls, xml):
        ed_name = xml.find('title').text
        start_date = parse_date(xml.find('start').text)
        end_date = parse_date(xml.find('end').text)
        visible_from = datetime.date(year=start_date.year - 1, month=8, day=1)
        visible_until = datetime.date(year=start_date.year, month=7, day=31)
        editions = cls.objects.filter(name=ed_name)
        if len(editions):
            edition = editions[0]
        else:
            edition = cls(name=ed_name)  # create if required
        edition.start_date = start_date
        edition.end_date = end_date
        edition.visible_from = visible_from
        edition.visible_until = visible_until
        edition.save()
        return edition

    @classmethod
    def init_generic_tasks(cls):
        edition = cls.get_current()
        if edition:
            generic_task_tree = ET.parse('volunteers/init_data/generic_tasks.xml')
            generic_task_root = generic_task_tree.getroot()
            for task in generic_task_root.findall('task'):
                Task.create_from_xml(task, edition)

    @classmethod
    def create_from_task_list(cls, file_name):
        edition = cls.get_current()
        if edition:
            generic_task_tree = ET.parse(file_name)
            generic_task_root = generic_task_tree.getroot()
            for task in generic_task_root.findall('task'):
                Task.create_from_xml(task, edition)

    @classmethod
    def sync_with_penta(cls):
        penta_url = settings.SCHEDULE_SYNC_URI
        response = urllib.request.urlopen(penta_url)
        penta_xml = response.read()
        root = ET.fromstring(penta_xml)
        ###########
        # Edition #
        ###########
        ed = root.find('conference')
        edition = cls.penta_create_or_update(ed)

        #########
        # Talks #
        #########
        days = root.findall('day')
        for day in days:
            day_date = parse_date(day.get('date'))
            rooms = day.findall('room')
            for room in rooms:
                room_name = room.get('name')
                if edition.digital_edition:
                    needs_hosting = False
                    if room_name[0] in ['L', 'M'] or room_name in ["D.blockchain"]:
                        needs_hosting = True
                    events = room.findall('event')
                    for event in events:
                        talk = Talk.penta_create_or_update(event, edition, day_date)
                        if needs_hosting:
                            Task.create_or_update_from_talk(edition, talk, 'Hosting', [1, 2, 3])
                else:
                    # Lightning talks are done manually since the time slots are so small.
                    needs_heralding = False
                    needs_video = False

                    if room_name in ['Janson', 'K.1.105 (La Fontaine)']:
                        needs_heralding = True
                        needs_video = getattr(settings, 'IMPORT_VIDEO_TASKS', True)

                    events = room.findall('event')
                    for event in events:
                        talk = Talk.penta_create_or_update(event, edition, day_date)
                        ######################
                        # Tasks, if required #
                        ######################
                        if needs_heralding:
                            Task.create_or_update_from_talk(edition, talk, 'Heralding', [3, 2, 5])
                        if needs_video:
                            Task.create_or_update_from_talk(edition, talk, 'Video', [1, 1, 1])


"""
A track is a collection of talks, grouped around one single
concept or subject.
"""


class Track(models.Model):
    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')
        ordering = ['date', 'start_time', 'title']

    def __str__(self):
        return self.title

    title = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    edition = models.ForeignKey(Edition, default=Edition.get_current().pk if Edition.get_current() else None, on_delete=PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    # end_time = models.TimeField()


# class Talk(models.Model, HasLinkField):
class Talk(models.Model):
    class Meta:
        verbose_name = _('Talk')
        verbose_name_plural = _('Talks')
        ordering = ['date', 'start_time', '-end_time', 'title']

    def __str__(self):
        return self.title

    ext_id = models.CharField(max_length=16)  # ID from where we synchronise
    track = models.ForeignKey(Track, related_name="talks", on_delete=CASCADE)
    title = models.CharField(max_length=256)
    speaker = models.CharField(max_length=128)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    volunteers = models.ManyToManyField('Volunteer', through='VolunteerTalk', blank=True)

    def assigned_volunteers(self):
        return self.volunteers.count()

    def link(self):
        return 'Link'

    @classmethod
    def penta_create_or_update(cls, xml, edition, day_date):
        event_id = xml.get('id')
        talks = cls.objects.filter(ext_id=event_id)
        if len(talks):
            talk = talks[0]
        else:
            talk = cls(ext_id=event_id)
        start_txt = xml.find('start').text
        dur_txt = xml.find('duration').text
        (talk_start, talk_end) = parse_hour_duration(start_txt, dur_txt)
        track_name = xml.find('track').text
        tracks = Track.objects.filter(title=track_name, edition=edition)
        if len(tracks):
            track = tracks[0]
        else:
            track = Track(title=track_name, edition=edition, date=day_date, start_time=talk_start)
        if day_date < track.date:
            track.date = day_date
        if talk_start < track.start_time:
            track.start_time = talk_start
        track.save()
        talk.track = track
        talk.title = xml.find('title').text
        talk.description = xml.find('description').text or ''
        talk.date = day_date
        (talk.start_time, talk.end_time) = (talk_start, talk_end)
        persons = xml.find('persons')
        people = []
        if len(persons):
            for person in persons.findall('person'):
                people.append(person.text)
            speakers_str = ', '.join(people)
            talk.speaker = speakers_str
        talk.save()
        return talk


"""
Categories are things like buildup, cleanup, moderation, ...
"""


class TaskCategory(models.Model):
    class Meta:
        verbose_name = _('Task Category')
        verbose_name_plural = _('Task Categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    active = models.BooleanField(default=True)

    def assigned_volunteers(self):
        return self.volunteer_set.count()

    def link(self):
        return 'Link'

    @classmethod
    def create_or_update_named(cls, name):
        categories = TaskCategory.objects.filter(name=name)
        if len(categories):
            category = categories[0]
        else:
            category = cls(name=name)
            category.save()
        return category


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

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50)
    description = models.TextField()
    category = models.ForeignKey(TaskCategory, on_delete=PROTECT)
    primary = models.ForeignKey(User, default=1, limit_choices_to={'is_staff': True}, on_delete=PROTECT)

    def link(self):
        return 'Link'

    @classmethod
    def create_or_update_named(cls, name):
        templates = cls.objects.filter(name=name)
        if len(templates):
            template = templates[0]
        else:
            template = cls(name=name)
            category = TaskCategory.create_or_update_named(name)
            template.category = category
            template.save()
        return template


"""
Contains the specifics of an instance of a task. It's based on a task template
but it can override the name and description, yet not the category.
"""


# class Task(models.Model, HasLinkField):
class Task(models.Model):
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['date', 'start_time', '-end_time', 'name']

    def __str__(self):
        day = self.date.strftime('%a')
        start = self.start_time.strftime('%H:%M')
        end = self.end_time.strftime('%H:%M')
        return "%s - %s (%s, %s - %s)" % (self.edition.name, self.name, day, start, end)

    name = models.CharField(max_length=300)
    # For auto-importing; otherwise we can't have multiple cloak room and
    # infodesk tasks if we do a simple name search in create_from_xml
    counter = models.CharField(max_length=2)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    nbr_volunteers = models.IntegerField(default=0)
    nbr_volunteers_min = models.IntegerField(default=0)
    nbr_volunteers_max = models.IntegerField(default=0)
    edition = models.ForeignKey(Edition, default=Edition.get_current().pk if Edition.get_current() else None, on_delete=PROTECT)
    template = models.ForeignKey(TaskTemplate, on_delete=PROTECT)
    volunteers = models.ManyToManyField('Volunteer', through='VolunteerTask', blank=True)
    # Only for heralding, or possible future tasks related
    # to a specific talk.
    talk = models.ForeignKey(Talk, blank=True, null=True, on_delete=CASCADE)

    def assigned_volunteers(self):
        # use the annotated volunteers_count if available
        # You should request tasks with Task.objects.annotate(volunteers_count=Count(volunteers)
        # note: in a more recent django version this construct is no longer
        # required and we can just return self.volunteers__count

        if hasattr(self, "volunteers__count"):
            return self.volunteers__count
        else:
            return self.volunteers.count()

    def link(self):
        return 'Link'

    # Create task from talks.
    # @param volunteers= list/tuple of required number of volunteers, in order:
    #        ideal, min, max
    @classmethod
    def create_or_update_from_talk(cls, edition, talk, task_type, volunteers):
        tasks = cls.objects.filter(talk=talk, template__name=task_type)
        templates = TaskTemplate.objects.filter(name=task_type)
        if len(templates):
            template = templates[0]
        else:
            template = TaskTemplate(name=task_type)
            categories = TaskCategory.objects.filter(name=task_type)
            if len(categories):
                category = categories[0]
            else:
                category = TaskCategory(name=task_type)
                category.save()
            template.category = category
            template.save()
        if len(tasks):
            task = tasks[0]
        else:
            task = cls(talk=talk, template=template)
        task.template = template
        task.name = '%s: %s' % (task_type, talk.title)
        task.date = talk.date
        task.start_time = talk.start_time
        task.end_time = talk.end_time
        task.edition = edition
        task.nbr_volunteers = volunteers[0]
        task.nbr_volunteers_min = volunteers[1]
        task.nbr_volunteers_max = volunteers[2]
        task.save()
        return task

    @classmethod
    def create_from_xml(cls, xml, edition):
        template_str = xml.get('template')
        template = TaskTemplate.create_or_update_named(template_str)
        name = xml.find('name').text
        counter = xml.find('counter').text
        tasks = cls.objects.filter(name=name, counter=counter, template=template, edition=edition)
        if len(tasks):
            task = tasks[0]
            # In this specific model I do not want to update after initial import
            return task
        else:
            task = cls(name=name, counter=counter, template=template, edition=edition)
        task.description = xml.find('description').text
        day_offset = int(xml.find('day').text)
        task.date = edition.start_date + datetime.timedelta(days=day_offset)
        task.start_time = parse_time(xml.find('start_time').text)
        task.end_time = parse_time(xml.find('end_time').text)
        task.nbr_volunteers = int(xml.find('nbr_volunteers').text)
        task.nbr_volunteers_min = int(xml.find('nbr_volunteers_min').text)
        task.nbr_volunteers_max = int(xml.find('nbr_volunteers_max').text)
        task.save()
        return task

    @property
    def status(self):
        """ Give status of a task"""
        if self.assigned_volunteers() >= self.nbr_volunteers_max:
            return "FULL"
        if self.assigned_volunteers() >= self.nbr_volunteers:
            return "OK"
        if self.assigned_volunteers() >= self.nbr_volunteers_min:
            return "MANAGEABLE"
        else:
            return "NEEDED"

    @property
    def status_color(self):
        colors = {
            "FULL": "blue",
            "OK": "green",
            "MANAGEABLE": "grey",
            "NEEDED": "red"
        }
        return colors[self.status]

"""
table to contain the language names and ISO codes
"""


class Language(models.Model):
    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

    def __str__(self):
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

    def __str__(self):
        return self.user.username

    ratings = (
        (0, 'No longer welcome'),
        (1, 'Poor'),
        (2, 'Not great'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Superb'),
    )

    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='volunteer', on_delete=CASCADE)
    # Categories in which they're interested to help out.
    # Tasks for which they've signed up.
    tasks = models.ManyToManyField(Task, through='VolunteerTask', blank=True)
    editions = models.ManyToManyField(Edition, through='VolunteerStatus', blank=True)
    signed_up = models.DateField(default=datetime.date.today)
    about_me = models.TextField(_('about me'), blank=True)
    mobile_nbr = models.CharField('Mobile Phone', max_length=30, blank=True, null=True,
                                  help_text="We won't share this, but we need it in case we"
                                            " need to contact you in a pinch during the event.")
    private_staff_rating = models.IntegerField(null=True, blank=True, choices=ratings)
    private_staff_notes = models.TextField(null=True, blank=True)
    penta_account_name = models.TextField('Your Pentabarf account name (penta.fosdem.org)', null=True,
                                          blank=True, max_length=256, help_text="We need this to link your volunteers account from Pentabarf to participate in heralding/hosting a digital edition.")


    # Just here for the admin interface.
    def full_name(self):
        return " ".join([self.user.first_name, self.user.last_name])

    def email(self):
        return self.user.email

    # Dr. Manhattan detection: is this person capable of being in multiple places at once?
    def detect_dr_manhattan(self):
        retval = [False, []]
        current_tasks = self.tasks.filter(edition=Edition.get_current())
        dates = sorted(list(set([x.date for x in current_tasks])))
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

    def vcard(self):
        card = vobject.vCard()
        card_props = [
            ('n', vobject.vcard.Name(family=self.user.last_name, given=self.user.first_name)),
            ('fn', '%s %s' % (self.user.first_name, self.user.last_name)),
            ('email', self.user.email),
            ('tel', self.mobile_nbr, 'cell'),
            ('categories', ['FOSDEM Volunteer']),
        ]
        for card_prop in card_props:
            vkey = card.add(card_prop[0])
            vkey.value = card_prop[1]
            if len(card_prop) > 2:
                vkey.type_param = card_prop[2]
        return card.serialize()

    def mail_schedule(self):
        subject = "FOSDEM Volunteers: your schedule"
        message_header = []
        message_header.extend(['Dear %s,' % (self.user.first_name), ''])
        edition = Edition.get_current()
        message_header.extend(['Here is your schedule for %s:' % (edition.name,), ''])
        message_body = []
        for task in self.tasks.filter(edition=Edition.get_current()):
            message_body.extend(["%s, %s-%s: %s" % (
                task.date.strftime('%a'),
                task.start_time,
                task.end_time,
                task.name,
            )])
        message_footer = [
            '',
            'Kind regards,',
            'FOSDEM Volunteers Team'
        ]
        message_txt = '\n'.join(message_header + message_body + message_footer)
        # Uncommenting html stuff for now; it's only in django development ATM
        # message_html = '<br/>'.join(message_header)
        # message_html += '<ul style="font-family: Courier New, monospace"><li>'
        # message_html += '</li><li>'.join(message_body)
        # message_html += '</li></ul>'
        # send_mail(subject, message_txt, settings.DEFAULT_FROM_EMAIL,
        #     [self.user.email], html_message=message_html, fail_silently=False)
        send_mail(subject, message_txt, settings.DEFAULT_FROM_EMAIL,
                  [self.user.email], fail_silently=False)

    def mail_user_created_for_you(self):
        subject = 'FOSDEM Volunteers: user created for you'
        message = [
            'Dear {0},'.format(self.user.first_name),
            '',
            'An account was created on volunteers.fosdem.org for you, probably during FOSDEM.',
            'Please reset your password via https://volunteers.fosdem.org/volunteers/password/reset/ .',
            '',
            'Kind regards,',
            'FOSDEM Volunteers Team'
        ]
        send_mail(subject, '\n'.join(message), settings.DEFAULT_FROM_EMAIL, [self.user.email],
                  fail_silently=False)

    def check_mugshot(self):
        mugshot_url = self.get_mugshot_url()
        # We only get None for mugshot_url if userena is not set up to use
        # gravatar fallback and no mughot has been uploaded.
        if not mugshot_url:
            return False
        # OK, we either have a gravatar, or an uploaded pic.
        elif 'gravatar.com' not in mugshot_url:
            return True
        # Right, definitely a gravatar then... Real, or auto-generated?
        # Code lifted from http://mcnearney.net/blog/2010/2/14/creating-django-gravatar-template-tag-part-1/
        GRAVATAR_DOMAIN = 'gravatar.com'
        GRAVATAR_PATH = '/avatar/'
        gravatar_hash = hashlib.md5(self.user.email.encode('utf-8').strip().lower()).hexdigest()
        query = urllib.parse.urlencode({
            'gravatar_id': gravatar_hash,
            's': 1,
            'default': '/'
        })
        full_path = '%s?%s' % (GRAVATAR_PATH, query)
        try:
            if os.environ.get('HTTPS_PROXY'):
                proxy_host, proxy_port = os.environ.get('HTTPS_PROXY').split('//')[1].split(':')
                proxy_port = int(proxy_port)
                conn = http.client.HTTPSConnection(proxy_host, proxy_port, timeout=5)
                conn.set_tunnel(GRAVATAR_DOMAIN)
            elif os.environ.get('HTTP_PROXY'):
                proxy_host, proxy_port = os.environ.get('HTTP_PROXY').split('//')[1].split(':')
                proxy_port = int(proxy_port)
                conn = http.client.HTTPConnection(proxy_host, proxy_port, timeout=5)
                conn.set_tunnel(GRAVATAR_DOMAIN)
            else:
                conn = http.client.HTTPConnection(GRAVATAR_DOMAIN, timeout=5)
            conn.request('HEAD', full_path)
            response = conn.getresponse()
            if response.status == 302:
                return False
            else:
                return True
        except:
            # Don't bug them if the connection can't be established
            return True


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

    def __str__(self):
        return '%s %s - %s: %s' % (self.volunteer.user.first_name,
                                   self.volunteer.user.last_name, self.edition.year,
                                   'Yes' if self.active else 'No')

    active = models.BooleanField()
    volunteer = models.ForeignKey(Volunteer, on_delete=CASCADE)
    edition = models.ForeignKey(Edition, default=Edition.get_current().pk if Edition.get_current() else None, on_delete=PROTECT)


"""
M2M tables because I want to have the relationship on both model admin pages
"""


class VolunteerTask(models.Model):
    class Meta:
        verbose_name = _('VolunteerTask')
        verbose_name_plural = _('VolunteerTasks')

    def __str__(self):
        return self.task.name

    volunteer = models.ForeignKey(Volunteer, on_delete=CASCADE)
    task = models.ForeignKey(Task, on_delete=CASCADE)


"""
link table between volunteers and languages
"""


class VolunteerLanguage(models.Model):
    class Meta:
        verbose_name = _('VolunteerLanguage')
        verbose_name_plural = _('VolunteerLanguages')

    def __str__(self):
        return language.name.name

    volunteer = models.ForeignKey(Volunteer, on_delete=CASCADE)
    language = models.ForeignKey(Language, on_delete=CASCADE)


"""
link table between volunteers and talks
"""


class VolunteerTalk(models.Model):
    class Meta:
        verbose_name = _('VolunteerTalk')
        verbose_name_plural = _('VolunteerTalks')

    def __str__(self):
        return self.talk.name

    volunteer = models.ForeignKey(Volunteer, on_delete=CASCADE)
    talk = models.ForeignKey(Talk, on_delete=CASCADE)


@receiver(post_save, sender=VolunteerTask)
def save_penta(sender, instance, **kwargs):
    if instance.task.talk_id is None and instance.task.template.name.lower() not in ['Infodesk'.lower()]:
        return
    if instance.task.template.name.lower() in ['Infodesk'.lower()]:
        # Harcoded because this works and will save me time
        if instance.task.date.weekday() == datetime.datetime.strptime('2021-02-06', '%Y-%m-%d').weekday():
            # Saturday
            event_id = '11762'
        else:
            # Sunday
            event_id = '11763'
    else:
        event_id = instance.task.talk.ext_id
    account_name = instance.volunteer.penta_account_name

    logger = logging.getLogger("pentabarf")
    logger.debug("Values in insert: %s, %s" % (event_id, account_name))
    try:
        with connections['pentabarf'].cursor() as cursor:
            cursor.execute("""
            insert into event_person (event_id, person_id, event_role,remark)
            VALUES (%s,(select person_id from auth.account where login_name = %s),'host','volunteer')
            on conflict on constraint event_person_event_id_person_id_event_role_key do nothing;
            """, (event_id, account_name))
    except Exception as err:
        logger.exception(err)


@receiver(post_delete, sender=VolunteerTask)
def delete_volunteertask(sender, instance, **kwargs):
    if instance.task.talk_id is None:
        return
    event_id = instance.task.talk.ext_id
    account_name = instance.volunteer.penta_account_name

    logger = logging.getLogger("pentabarf")
    logger.debug("Values in delete: %s, %s" % (event_id, account_name))
    try:
        with connections['pentabarf'].cursor() as cursor:
            cursor.execute("delete from event_person where event_id=%s and person_id=(select person_id from auth.account where login_name = %s) and event_role='host' and remark='volunteer';", (event_id, account_name))
    except Exception as err:
        logger.exception(err)
