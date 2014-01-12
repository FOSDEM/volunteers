from models import Volunteer, VolunteerTask, VolunteerCategory, VolunteerTalk, TaskCategory, Task, Track, Talk
from forms import EditProfileForm

from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404

from userena.utils import get_user_model
from userena.decorators import secure_required
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView, get_profile_model

from guardian.decorators import permission_required_or_403

def promo(request):
    return render(request, 'static/promo.html')

@secure_required
@permission_required_or_403('talks_edit')
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

@secure_required
@permission_required_or_403('tasks_edit')
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

def task_list_detailed(request, username):

    if request.POST:
        return redirect('/tasks/'+username)

    context = {}
    # get the requested users tasks
    context['tasks'] = Task.objects.filter(volunteers__user__username=username)

    return render(request, 'volunteers/tasks_detailed.html', context)

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