from models import Volunteer, VolunteerTask, VolunteerCategory, TaskCategory, Task, Track, Talk
from forms import EditProfileForm

from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404

from userena.utils import get_user_model
from userena.decorators import secure_required
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView, get_profile_model

from guardian.decorators import permission_required_or_403

def promo(request):
    return render(request, 'static/promo.html')

def talk_list(request):
    context = {}
    return render(request, 'volunteers/talks.html', context)

def task_list(request):
    # get the signed in volunteer
    volunteer = Volunteer.objects.get(user=request.user)

    # when the user submitted the form
    if request.method == 'POST':
        # get the checked tasks
        ids = request.POST.getlist('task')

        # go trough all the checked tasks
        for task in Task.objects.filter(id__in=ids):
            # when the volunteer is not assigned to this task
            if volunteer not in task.volunteers.all():
                # add him/her
                VolunteerTask(task=task, volunteer=volunteer).save()

        # go trough all the not checked tasks
        for task in Task.objects.exclude(id__in=ids):
            # delete him/her
            VolunteerTask.objects.filter(task=task, volunteer=volunteer).delete()
    
    # get the categories the volunteer is interested in
    categories = TaskCategory.objects.filter(volunteer=request.user)
    # get the interesting and other tasks
    context = {}
    context['volunteer'] = volunteer
    context['interesting_tasks'] = list(Task.objects.filter(template__category__in=categories).annotate(volunteers_assigned=Count('volunteers')))
    context['other_tasks'] = Task.objects.exclude(template__category__in=categories).annotate(volunteers_assigned=Count('volunteers'))
    
    context['checked'] = {}
    for task in context['interesting_tasks']:
        context['checked'][task.id] = 'checked' if volunteer in task.volunteers.all() else ''

    for task in context['other_tasks']:
        context['checked'][task.id] = 'checked' if volunteer in task.volunteers.all() else ''

    return render(request, 'volunteers/tasks.html', context)

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
    user = get_object_or_404(get_user_model(),
                             username__iexact=username)

    profile = user.get_profile()

    user_initial = {'first_name': user.first_name,
                    'last_name': user.last_name}

    form = edit_profile_form(instance=profile, initial=user_initial)

    if request.method == 'POST':
        form = edit_profile_form(request.POST, request.FILES, instance=profile,
                                 initial=user_initial)

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
                messages.success(request, _('Your profile has been updated.'),
                                 fail_silently=True)

            if success_url:
                # Send a signal that the profile has changed
                userena_signals.profile_change	.send(sender=None,
                                                    user=user)
                redirect_to = success_url
            else: redirect_to = reverse('userena_profile_detail', kwargs={'username': username})
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    extra_context['profile'] = profile
    return ExtraContextTemplateView.as_view(template_name=template_name,
                                            extra_context=extra_context)(request)
