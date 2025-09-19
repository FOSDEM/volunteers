from .models import Volunteer, VolunteerTask, VolunteerTalk, TaskCategory, TaskTemplate, Task, Track, \
    Talk, Edition
from .forms import EditProfileForm, SignupForm, EventSignupForm

from django.contrib import messages
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from collections import OrderedDict as SortedDict
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth import get_user_model

from userena.forms import SignupFormOnlyEmail
from userena.decorators import secure_required
from userena import signals as userena_signals
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView, get_profile_model

from guardian.decorators import permission_required_or_403

import csv

from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.utils.html import escape


def check_profile_completeness(request, volunteer):
    if request.user != volunteer.user:
        return True

    if not volunteer.mobile_nbr:
        messages.warning(request, _(
            "Hey there! It seems you didn't give us a phone number. Please update your profile, to make sure we can contact you if the network fails..."),
                         fail_silently=True)
    if not volunteer.check_mugshot():
        messages.warning(request, _(
            "Looks like we don't have your beautiful smile in our system. Be so kind to upload a mugshot in your profile page. :)"),
                         fail_silently=True)


def faq(request):
    return render(request, 'static/faq.html')


def privacy_policy(request):
    return render(request, 'static/privacy_policy.html')


def promo(request):
    return render(request, 'static/promo.html')


@login_required
def talk_detailed(request, talk_id):
    talk = get_object_or_404(Talk, id=talk_id)
    context = {'talk': talk}
    return render(request, 'volunteers/talk_detailed.html', context)


def task_detailed(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    context = {'task': task}
    return render(request, 'volunteers/task_detailed.html', context)


@login_required
def talk_list(request):
    # get the signed in volunteer
    volunteer = Volunteer.objects.get(user=request.user)

    # when the user submitted the form
    if request.method == 'POST':
        # get the checked tasks
        talk_ids = request.POST.getlist('talk')

        # go trough all the talks that were checked
        for talk in Talk.objects.filter(id__in=talk_ids):
            # add the volunteer to the talk when he/she is not added
            VolunteerTalk.objects.get_or_create(talk=talk, volunteer=volunteer)

        # delete all the not checked talks
        VolunteerTalk.objects.filter(volunteer=volunteer).exclude(talk_id__in=talk_ids).delete()

        # show success message when enabled
        if userena_settings.USERENA_USE_MESSAGES:
            messages.success(request, _('Your talks have been updated.'), fail_silently=True)

        # redirect to prevent repost
        return redirect('talk_list')

    # group the talks according to tracks
    context = {'talks': [], 'checked': {}}

    talks = Talk.objects.select_related('track').filter(track__edition=Edition.get_current()).order_by('track__title', 'date', 'start_time')

    context['talks'] = talks

    # mark checked, attending talks
    for talk in Talk.objects.filter(volunteers=volunteer):
        context['checked'][talk.id] = 'checked'

    return render(request, 'volunteers/talks.html', context)


@login_required
def category_schedule_list(request):
    categories = TaskCategory.objects.filter(active=True)
    context = {'categories': SortedDict.fromkeys(categories, [])}
    for category in context['categories']:
        context['categories'][category] = TaskTemplate.objects.filter(category=category)
    return render(request, 'volunteers/category_schedule_list.html', context)


@login_required
def task_schedule(request, template_id):
    template = TaskTemplate.objects.filter(id=template_id)[0]
    tasks = Task.objects.annotate(volunteers__count=Count("volunteer")).filter(template=template, edition=Edition.get_current()).order_by('date', 'start_time', 'end_time')
    context = {
        'template': template,
        'tasks': SortedDict.fromkeys(tasks, {}),
    }
    for task in context['tasks']:
        context['tasks'][task] = Volunteer.objects.filter(tasks=task)
    return render(request, 'volunteers/task_schedule.html', context)


@login_required
def task_schedule_csv(request, template_id):
    template = TaskTemplate.objects.filter(id=template_id)[0]
    tasks = Task.objects.annotate(volunteers__count=Count("volunteer")).filter(template=template, edition=Edition.get_current()).order_by('date', 'start_time', 'end_time')
    response = HttpResponse(content_type='text/csv')
    filename = "schedule_%s.csv" % template.name
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    writer = csv.writer(response)
    writer.writerow(['Task', 'Volunteers', 'Day', 'Start', 'End', 'Volunteer', 'Nick', 'Email', 'Mobile', 'Matrix_id'])
    for task in tasks:
        row = [
            task.name,
            "(%s/%s)" % (task.assigned_volunteers(), task.nbr_volunteers),
            task.date.strftime('%a'),
            task.start_time.strftime('%H:%M'),
            task.end_time.strftime('%H:%M'),
            '', '', '', '',''
        ]
        writer.writerow(row)
        volunteers = Volunteer.objects.filter(tasks=task)
        for number, volunteer in enumerate(volunteers):
            row = [
                '', '', '', '', '',
                "%s %s" % (volunteer.user.first_name, volunteer.user.last_name),
                volunteer.user.username,
                volunteer.user.email,
                volunteer.mobile_nbr,
                volunteer.matrix_id
            ]
            writer.writerow(row)
        row = [''] * 10
        writer.writerow(row)
    return response


def task_list(request):
    # get the signed in volunteer

    current_tasks = Task.objects.annotate(
        volunteers__count=Count("volunteer")).filter(
        edition=Edition.get_current()).order_by('date', 'start_time', 'end_time')


    if request.user.is_authenticated:
        volunteer = Volunteer.objects.get(user=request.user)
        current_tasks = current_tasks.prefetch_related("volunteers").prefetch_related("volunteers__user")
    else:
        volunteer = None
        is_dr_manhattan = False

    if volunteer:
        is_dr_manhattan, dr_manhattan_task_sets = volunteer.detect_dr_manhattan()
        dr_manhattan_task_ids = [x.id for x in set.union(*dr_manhattan_task_sets)] if dr_manhattan_task_sets else []
        ok_tasks = current_tasks.exclude(id__in=dr_manhattan_task_ids)
    else:
        ok_tasks = current_tasks
    days = sorted(list(set([x.date for x in current_tasks])))

    # when the user submitted the form
    if request.method == 'POST' and volunteer:
        # get the checked tasks
        task_ids = request.POST.getlist('task')

        # unchecked boxes, delete him/her from the task
        VolunteerTask.objects.exclude(task_id__in=task_ids).filter(volunteer=volunteer).delete()

        # checked boxes, add the volunteer to the tasks when he/she is not added
        for task in current_tasks.filter(id__in=task_ids):
            VolunteerTask.objects.get_or_create(task=task, volunteer=volunteer)

        # show success message when enabled
        if userena_settings.USERENA_USE_MESSAGES:
            messages.success(request, _('Your tasks have been updated.'), fail_silently=True)

        # redirect to prevent repost
        return redirect('task_list')

    # get the preferred and other tasks, preserve key order with srteddict for view
    context = {
        'tasks': SortedDict({}),
        'checked': {},
        'attending': {},
        'is_dr_manhattan': is_dr_manhattan,
        'setup_for_current_year_complete': getattr(settings, 'SETUP_FOR_CURRENT_YEAR_COMPLETE', False),
    }
    # get the categories the volunteer is interested in
    if volunteer:
        categories_by_task_pref = {
            'tasks': TaskCategory.objects.filter(active=True),
        }
        context['volunteer'] = volunteer
        context['dr_manhattan_task_sets'] = dr_manhattan_task_sets
        context['tasks']['tasks'] = SortedDict.fromkeys(days, {})
    else:
        categories_by_task_pref = {
            # 'preferred tasks': [],
            'tasks': TaskCategory.objects.filter(active=True),
        }
        context['tasks']['tasks'] = SortedDict.fromkeys(days, {})
    context['user'] = request.user

    context['user_in_penta'] = hasattr(request.user, 'volunteer') and request.user.volunteer.penta_account_name is not None and len(request.user.volunteer.penta_account_name)>0
    for category_group in context['tasks']:
        for day in context['tasks'][category_group]:
            context['tasks'][category_group][day] = SortedDict.fromkeys(categories_by_task_pref[category_group], [])
            for category in context['tasks'][category_group][day]:
                dct = ok_tasks.filter(template__category=category, date=day)
                context['tasks'][category_group][day][category] = dct

    # mark checked, attending tasks
    if volunteer:
        for task in current_tasks:
            context['checked'][task.id] = 'checked' if volunteer in task.volunteers.all() else ''
            context['attending'][task.id] = False

        # take the moderation tasks to talks the volunteer is attending
        for task in current_tasks.filter(talk__volunteers=volunteer):
            context['attending'][task.id] = True
        check_profile_completeness(request, volunteer)
    else:
        for task in current_tasks:
            context['attending'][task.id] = False

    return render(request, 'volunteers/tasks.html', context)


@user_passes_test(lambda u: u.is_superuser)
def event_sign_on(request):
    current_tasks = Task.objects.filter(edition=Edition.get_current())
    ok_tasks = current_tasks
    days = sorted(list(set([x.date for x in current_tasks])))
    signup_form = EventSignupForm
    # when the user submitted the form
    if request.method == 'POST':
        # create volunteer
        form = signup_form(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # Send the signup complete signal
            userena_signals.signup_complete.send(sender=None, user=user)

            volunteer = Volunteer.objects.get(user=user)
            # get the checked tasks
            task_ids = request.POST.getlist('task')

            # unchecked boxes, delete him/her from the task
            for task in current_tasks.exclude(id__in=task_ids):
                VolunteerTask.objects.filter(task=task, volunteer=volunteer).delete()

            # checked boxes, add the volunteer to the tasks when he/she is not added
            for task in current_tasks.filter(id__in=task_ids):
                VolunteerTask.objects.get_or_create(task=task, volunteer=volunteer)
            # Send tasks
            volunteer.mail_schedule()
            # Send reset password mail
            volunteer.mail_user_created_for_you()
            # show success message when enabled
            if userena_settings.USERENA_USE_MESSAGES:
                messages.success(request, _('Tasks for {0} have been updated.'.format(user.username)),
                                 fail_silently=True)

    # get the preferred and other tasks, preserve key order with srteddict for view
    context = {
        'tasks': SortedDict({}),
        'checked': {},
        'attending': {},
        'is_dr_manhattan': False,
        'setup_for_current_year_complete': getattr(settings, 'SETUP_FOR_CURRENT_YEAR_COMPLETE', False),
    }
    # get the categories the volunteer is interested in
    categories_by_task_pref = {
        # 'preferred tasks': [],
        'tasks': TaskCategory.objects.filter(active=True),
    }
    context['tasks']['tasks'] = SortedDict.fromkeys(days, {})
    context['user'] = request.user
    for category_group in context['tasks']:
        for day in context['tasks'][category_group]:
            context['tasks'][category_group][day] = SortedDict.fromkeys(categories_by_task_pref[category_group], [])
            for category in context['tasks'][category_group][day]:
                dct = ok_tasks.filter(template__category=category, date=day)
                context['tasks'][category_group][day][category] = dct

    # Sign up during the event
    context['form'] = signup_form
    # mark checked, attending tasks
    for task in current_tasks:
        context['attending'][task.id] = False

    return render(request, 'volunteers/event_sign_on.html', context)


@login_required
def render_to_pdf(request, template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest = response)
    if not pisa_status.err:
        return response
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


@login_required
def task_list_detailed(request, username):
    context = {}
    current_tasks = Task.objects.filter(edition=Edition.get_current()).order_by('date', 'start_time', 'end_time')

    # get the requested users tasks
    context['tasks'] = current_tasks.filter(volunteers__user__username=username)
    context['user'] = request.user
    context['profile_user'] = User.objects.filter(username=username)[0]
    volunteer = Volunteer.objects.filter(user__username=username)[0]
    context['volunteer'] = volunteer
    check_profile_completeness(request, volunteer)

    if request.POST:
        if 'print_pdf' in request.POST:
            # create the HttpResponse object with the appropriate PDF headers.
            context.update({'pagesize': 'A4'})
            return render_to_pdf(request, 'volunteers/tasks_detailed.html', context)
        elif 'mail_schedule' in request.POST:
            volunteer.mail_schedule()
            messages.success(request, _('Your shedule has been mailed to %s.' % (volunteer.user.email,)),
                             fail_silently=True)

    return render(request, 'volunteers/tasks_detailed.html', context)


@secure_required
def signup(request, signup_form=SignupForm,
           template_name='userena/signup_form.html', success_url=None,
           extra_context=None):
    """
        Signup of an account.

        Signup requiring a username, email and password. After signup a user gets
        an email with an activation link used to activate their account. After
        successful signup redirects to ``success_url``.

        :param signup_form:
            Form that will be used to sign a user. Defaults to userena's
            :class:`SignupForm`.

        :param template_name:
            String containing the template name that will be used to display the
            signup form. Defaults to ``userena/signup_form.html``.

        :param success_url:
            String containing the URI which should be redirected to after a
            successful signup. If not supplied will redirect to
            ``userena_signup_complete`` view.

        :param extra_context:
            Dictionary containing variables which are added to the template
            context. Defaults to a dictionary with a ``form`` key containing the
            ``signup_form``.

        **Context**

        ``form``
            Form supplied by ``signup_form``.
    """
    # If signup is disabled, return 403
    if userena_settings.USERENA_DISABLE_SIGNUP:
        raise PermissionDenied

    # If no usernames are wanted and the default form is used, fallback to the
    # default form that doesn't display to enter the username.
    if userena_settings.USERENA_WITHOUT_USERNAMES and (signup_form == SignupForm):
        signup_form = SignupFormOnlyEmail

    form = signup_form()

    if request.method == 'POST':
        form = signup_form(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            # Send the signup complete signal
            userena_signals.signup_complete.send(sender=None, user=user)

            if success_url:
                redirect_to = success_url
            else:
                redirect_to = reverse('userena_signup_complete', kwargs={'username': user.username})

            # A new signed user should logout the old one.
            if request.user.is_authenticated:
                logout(request)

            if (userena_settings.USERENA_SIGNIN_AFTER_SIGNUP and
                    not userena_settings.USERENA_ACTIVATION_REQUIRED):
                user = authenticate(identification=user.email, check_password=False)
                login(request, user)

            return redirect(redirect_to)

    if not extra_context:
        extra_context = dict()
    extra_context['form'] = form
    return ExtraContextTemplateView.as_view(template_name=template_name, extra_context=extra_context)(request)


@secure_required
@login_required
@permission_required_or_403('change_profile', (get_profile_model(), 'user__username', 'username'))
def profile_edit(request, username, edit_profile_form=EditProfileForm,
                 template_name='userena/profile_form.html', success_url=None,
                 extra_context=None, **kwargs):
    """
        Edit profile.

        Edits a profile selected by the supplied username. First checks
        permissions if the user is allowed to edit this profile, if denied will
        show a 404. When the profile is successfully edited will redirect to
        ``success_url``.

        :param username:
            Username of the user which profile should be edited.

        :param edit_profile_form:

            Form that is used to edit the profile. The :func:`EditProfileForm.save`
            method of this form will be called when the form
            :func:`EditProfileForm.is_valid`.  Defaults to :class:`EditProfileForm`
            from userena.

        :param template_name:
            String of the template that is used to render this view. Defaults to
            ``userena/edit_profile_form.html``.

        :param success_url:
            Named URL which will be passed on to a django ``reverse`` function after
            the form is successfully saved. Defaults to the ``userena_detail`` url.

        :param extra_context:
            Dictionary containing variables that are passed on to the
            ``template_name`` template.  ``form`` key will always be the form used
            to edit the profile, and the ``profile`` key is always the edited
            profile.

        **Context**

        ``form``
            Form that is used to alter the profile.

        ``profile``
            Instance of the ``Profile`` that is edited.
    """
    user = get_object_or_404(get_user_model(), username__iexact=username)

    profile = user.volunteer

    user_initial = {'first_name': user.first_name, 'last_name': user.last_name}

    form = edit_profile_form(instance=profile, initial=user_initial)

    if request.method == 'POST':
        form = edit_profile_form(request.POST, request.FILES, instance=profile, initial=user_initial)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.save()

            if userena_settings.USERENA_USE_MESSAGES:
                messages.success(request, _('Your profile has been updated.'), fail_silently=True)

            if success_url:
                # Send a signal that the profile has changed
                userena_signals.profile_change.send(sender=None, user=user)
                redirect_to = success_url
            else:
                redirect_to = reverse('userena_profile_detail', kwargs={'username': username})
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    extra_context['profile'] = profile
    return ExtraContextTemplateView.as_view(template_name=template_name,
                                            extra_context=extra_context)(request)


@login_required
def profile_detail(request, username,
                   template_name=userena_settings.USERENA_PROFILE_DETAIL_TEMPLATE,
                   extra_context=None, **kwargs):
    """
        Detailed view of an user.

        :param username:
            String of the username of which the profile should be viewed.

        :param template_name:
            String representing the template name that should be used to display
            the profile.

        :param extra_context:
            Dictionary of variables which should be supplied to the template. The
            ``profile`` key is always the current profile.

        **Context**

        ``profile``
            Instance of the currently viewed ``Profile``.
    """
    user = get_object_or_404(get_user_model(), username__iexact=username)
    current_tasks = Task.objects.filter(edition=Edition.get_current()).order_by('date', 'start_time', 'end_time')


    profile_model = get_profile_model()
    try:
        profile = user.volunteer
    except profile_model.DoesNotExist:
        profile = profile_model.objects.create(user=user)

    if not profile.can_view_profile(request.user):
        raise PermissionDenied
    if not extra_context: extra_context = dict()
    extra_context['profile'] = user.volunteer
    extra_context['tasks'] = current_tasks.filter(volunteers__user=user)
    extra_context['hide_email'] = userena_settings.USERENA_HIDE_EMAIL
    check_profile_completeness(request, user.volunteer)
    return ExtraContextTemplateView.as_view(template_name=template_name, extra_context=extra_context)(request)


class ProfileListView(ListView):
    """ Lists all profiles """
    context_object_name = 'profile_list'
    page = 1
    paginate_by = 50
    template_name = userena_settings.USERENA_PROFILE_LIST_TEMPLATE
    extra_context = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ProfileListView, self).get_context_data(**kwargs)
        try:
            page = int(self.request.GET.get('page', None))
        except (TypeError, ValueError):
            page = self.page

        if userena_settings.USERENA_DISABLE_PROFILE_LIST \
                and not self.request.user.is_staff:
            raise Http404

        if not self.extra_context: self.extra_context = dict()

        context['page'] = page
        context['paginate_by'] = self.paginate_by
        context['extra_context'] = self.extra_context

        return context

    def get_queryset(self):
        profile_model = get_profile_model()
        queryset = profile_model.objects.get_visible_profiles(self.request.user).select_related().extra( \
            select={'lower_name': 'lower(first_name)'}).order_by('lower_name')
        return queryset
