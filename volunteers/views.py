from models import Volunteer, VolunteerTask, VolunteerCategory, VolunteerTalk, TaskCategory, Task, Track, Talk
from forms import EditProfileForm, SignupForm

from django.db.models import Count
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404

from userena.utils import get_user_model
from userena.forms import SignupFormOnlyEmail
from userena.decorators import secure_required
from userena import signals as userena_signals
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView, get_profile_model

from guardian.decorators import permission_required_or_403

def promo(request):
    return render(request, 'static/promo.html')

def talk_detailed(request, talk_id):
    talk = get_object_or_404(Talk, id=talk_id)
    context = { 'talk': talk }
    return render(request, 'volunteers/talk_detailed.html', context)

def task_detailed(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    context = { 'task': task }
    return render(request, 'volunteers/task_detailed.html', context)

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

        # go trough all the not checked tasks
        for talk in Talk.objects.exclude(id__in=talk_ids):
            # delete him/her
            VolunteerTalk.objects.filter(talk=talk, volunteer=volunteer).delete()

        # show success message when enabled
        if userena_settings.USERENA_USE_MESSAGES:
            messages.success(request, _('Your talks have been updated.'), fail_silently=True)

        # redirect to prevent repost
        return redirect('/talks')

    # group the talks according to tracks
    context = { 'tracks': {}, 'checked': {} }
    tracks = Track.objects.all()
    for track in tracks:
        context['tracks'][track.title] = Talk.objects.filter(track=track)

    # mark checked, attending talks
    for talk in Talk.objects.filter(volunteers=volunteer):
        context['checked'][talk.id] = 'checked'

    return render(request, 'volunteers/talks.html', context)

def task_list(request):
    # get the signed in volunteer
    volunteer = Volunteer.objects.get(user=request.user)

    # when the user submitted the form
    if request.method == 'POST':
        # get the checked tasks
        task_ids = request.POST.getlist('task')

        # checked boxes, add the volunteer to the tasks when he/she is not added
        for task in Task.objects.filter(id__in=task_ids):
            VolunteerTask.objects.get_or_create(task=task, volunteer=volunteer)

        # unchecked boxes, delete him/her from the task
        for task in Task.objects.exclude(id__in=task_ids):
            VolunteerTask.objects.filter(task=task, volunteer=volunteer).delete()

        # show success message when enabled
        if userena_settings.USERENA_USE_MESSAGES:
            messages.success(request, _('Your tasks have been updated.'), fail_silently=True)

        # redirect to prevent repost
        return redirect('/tasks')

    # get the categories the volunteer is interested in
    categories = TaskCategory.objects.filter(volunteer=request.user)
    # get the preferred and other tasks, preserve key order with srteddict for view
    context = { 'tasks': SortedDict({}), 'checked': {}, 'attending': {} }
    context['volunteer'] = volunteer
    context['tasks']['preferred tasks'] = Task.objects.filter(template__category__in=categories)
    context['tasks']['other tasks'] = Task.objects.exclude(template__category__in=categories)

    # mark checked, attending tasks
    for task in context['tasks']['preferred tasks']:
        context['checked'][task.id] = 'checked' if volunteer in task.volunteers.all() else ''
    for task in context['tasks']['other tasks']:
        context['checked'][task.id] = 'checked' if volunteer in task.volunteers.all() else ''

    # take the moderation tasks to talks the volunteer is attending
    for task in Task.objects.filter(talk__volunteers=volunteer):
        context['attending'][task.id] = True

    return render(request, 'volunteers/tasks.html', context)

import cStringIO as StringIO
import ho.pisa as pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from cgi import escape

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()

    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), mimetype='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))

def task_list_detailed(request, username):

    context = {}
    # get the requested users tasks
    context['tasks'] = Task.objects.filter(volunteers__user__username=username)

    if request.POST:
        # create the HttpResponse object with the appropriate PDF headers.
        return render_to_pdf('volunteers/tasks_detailed.html', { 'pagesize':'A4', 'tasks': context['tasks'], })

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

            if success_url: redirect_to = success_url
            else: redirect_to = reverse('userena_signup_complete', kwargs={'username': user.username})

            # A new signed user should logout the old one.
            if request.user.is_authenticated():
                logout(request)

            if (userena_settings.USERENA_SIGNIN_AFTER_SIGNUP and
                not userena_settings.USERENA_ACTIVATION_REQUIRED):
                user = authenticate(identification=user.email, check_password=False)
                login(request, user)

            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    return ExtraContextTemplateView.as_view(template_name=template_name, extra_context=extra_context)(request)

@secure_required
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

    profile = user.get_profile()

    user_initial = {'first_name': user.first_name, 'last_name': user.last_name}

    form = edit_profile_form(instance=profile, initial=user_initial)

    if request.method == 'POST':
        form = edit_profile_form(request.POST, request.FILES, instance=profile, initial=user_initial)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.save()
            # go trough all the task categories for this volunteer
            for category in TaskCategory.objects.all():
            	exists = VolunteerCategory.objects.filter(volunteer=profile, category=category)
                selected = form.cleaned_data.get('categories').filter(name=category.name)
                # when the category does not exist and was selected, add it
                if not exists and selected:
                    profilecategory = VolunteerCategory(volunteer=profile, category=category)
                    profilecategory.save()
                # when the category exists and was deselected, delete it
                elif exists and not selected:
                    profilecategory = VolunteerCategory.objects.filter(volunteer=profile, category=category)
                    profilecategory.delete()

            if userena_settings.USERENA_USE_MESSAGES:
                messages.success(request, _('Your profile has been updated.'), fail_silently=True)

            if success_url:
                # Send a signal that the profile has changed
                userena_signals.profile_change.send(sender=None, user=user)
                redirect_to = success_url
            else: redirect_to = reverse('userena_profile_detail', kwargs={'username': username})
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    extra_context['profile'] = profile
    return ExtraContextTemplateView.as_view(template_name=template_name,
                                            extra_context=extra_context)(request)

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

    profile_model = get_profile_model()
    try:
        profile = user.get_profile()
    except profile_model.DoesNotExist:
        profile = profile_model.objects.create(user=user)

    if not profile.can_view_profile(request.user):
        raise PermissionDenied
    if not extra_context: extra_context = dict()
    extra_context['profile'] = user.get_profile()
    extra_context['tasks'] = Task.objects.filter(volunteers__user=user)
    extra_context['hide_email'] = userena_settings.USERENA_HIDE_EMAIL
    return ExtraContextTemplateView.as_view(template_name=template_name, extra_context=extra_context)(request)