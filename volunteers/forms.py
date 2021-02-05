from volunteers.models import VolunteerTask, TaskCategory

from django import forms
from django.utils.translation import ugettext as _
import re

from userena.models import UserenaSignup
from userena import settings as userena_settings
from userena.utils import get_profile_model, get_user_model
import random
import string


class AddTasksForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=VolunteerTask.objects.none(), widget=forms.CheckboxSelectMultiple())


class EditTasksForm(forms.Form):
    date = forms.TimeField(label=_(u'Date'), required=True)
    start_time = forms.TimeField(label=_(u'Start time'), required=True)
    end_time = forms.TimeField(label=_(u'End time'), required=True)
    name = forms.CharField(label=_(u'Name'), max_length=30, required=True)
    description = forms.CharField(label=_(u'Description'), max_length=30, required=False, widget=forms.Textarea)


class EventSignupForm(forms.Form):
    first_name = forms.CharField(max_length=255, required=True, label=_('First name'))
    last_name = forms.CharField(max_length=255, required=True, label=_('Last name'))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'required', 'maxlength': 255}), label=_('E-mail'))

    @property
    def username(self):
        invalid_r = re.compile('[^A-Z]', flags=re.IGNORECASE)
        return '{0}{1}'.format(
            invalid_r.sub('', self.cleaned_data['first_name']),
            invalid_r.sub('', self.cleaned_data['last_name'])
        )

    def clean_email(self):
        """ Validate that the e-mail address is unique. """
        if get_user_model().objects.filter(email__iexact=self.cleaned_data['email']):
            if userena_settings.USERENA_ACTIVATION_REQUIRED \
                    and UserenaSignup.objects.filter(user__email__iexact=self.cleaned_data['email'])\
                    .exclude(activation_key=userena_settings.USERENA_ACTIVATED):
                raise forms.ValidationError(
                    _('This email is already in use but not confirmed. Please check your email for verification steps.')
                )
            raise forms.ValidationError(_('This email is already in use. Please supply a different email.'))
        return self.cleaned_data['email']

    def save(self):
        """ Creates a new user and account. Returns the newly created user. """

        new_user = UserenaSignup.objects.create_user(
            self.username,
            self.cleaned_data['email'],
            ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]),
            True,
            False
        )
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        return new_user


class SignupForm(forms.Form):
    """
        Form for creating a new user account.

        Validates that the requested username and e-mail is not already in use.
        Also requires the password to be entered twice.
    """
    USERNAME_RE = r'^[\.\w]+$'
    attrs_dict = {'class': 'required'}
    first_name = forms.CharField(max_length=30, required=True, label=_("First name"))
    last_name = forms.CharField(max_length=30, required=True, label=_("Last name"))
    username = forms.RegexField(regex=USERNAME_RE, max_length=30, widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={
                                    'invalid': _('Username must contain only letters, numbers, dots and underscores.')})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)), label=_("Email"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Create password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Repeat password"))

    def clean_username(self):
        """
            Validate that the username is alphanumeric and is not already in use.
            Also validates that the username is not listed in
            ``USERENA_FORBIDDEN_USERNAMES`` list.
        """
        try:
            user = get_user_model().objects.get(username__iexact=self.cleaned_data['username'])
        except get_user_model().DoesNotExist:
            pass
        else:
            if userena_settings.USERENA_ACTIVATION_REQUIRED and UserenaSignup.objects.filter(
                    user__username__iexact=self.cleaned_data['username']).exclude(
                    activation_key=userena_settings.USERENA_ACTIVATED):
                raise forms.ValidationError(_(
                    'This username is already taken but not confirmed. Please check your email for verification steps.'))
            raise forms.ValidationError(_('This username is already taken.'))
        if self.cleaned_data['username'].lower() in userena_settings.USERENA_FORBIDDEN_USERNAMES:
            raise forms.ValidationError(_('This username is not allowed.'))
        return self.cleaned_data['username']

    def clean_email(self):
        """ Validate that the e-mail address is unique. """
        if get_user_model().objects.filter(email__iexact=self.cleaned_data['email']):
            if userena_settings.USERENA_ACTIVATION_REQUIRED and UserenaSignup.objects.filter(
                    user__email__iexact=self.cleaned_data['email']).exclude(
                    activation_key=userena_settings.USERENA_ACTIVATED):
                raise forms.ValidationError(_(
                    'This email is already in use but not confirmed. Please check your email for verification steps.'))
            raise forms.ValidationError(_('This email is already in use. Please supply a different email.'))
        return self.cleaned_data['email']

    def clean(self):
        """
            Validates that the values entered into the two password fields match.
            Note that an error here will end up in ``non_field_errors()`` because
            it doesn't apply to a single field.
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_('The two password fields didn\'t match.'))
        return self.cleaned_data

    def save(self, activation_required=True):
        """ Creates a new user and account. Returns the newly created user. """

        first_name, last_name, username, email, password = (self.cleaned_data['first_name'],
                                                            self.cleaned_data['last_name'],
                                                            self.cleaned_data['username'],
                                                            self.cleaned_data['email'],
                                                            self.cleaned_data['password1'])

        new_user = UserenaSignup.objects.create_user(username, email, password,
                                                     not activation_required,
                                                     activation_required)
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()
        return new_user


class EditProfileForm(forms.ModelForm):
    """ Base form used for fields that are always required """
    first_name = forms.CharField(label=_(u'First name'), max_length=30, required=True)
    last_name = forms.CharField(label=_(u'Last name'), max_length=30, required=True)

    def __init__(self, *args, **kw):
        super(EditProfileForm, self).__init__(*args, **kw)
        # Put the first and last name at the top

    class Meta:
        model = get_profile_model()
        exclude = ['user', 'editions', 'tasks', 'signed_up', 'language', 'privacy', 'private_staff_rating',
                   'private_staff_notes', 'categories']
        fields = ['first_name', 'last_name', 'penta_account_name', 'mobile_nbr', 'about_me', 'mugshot']

    def save(self, force_insert=False, force_update=False, commit=True):
        profile = super(EditProfileForm, self).save(commit=commit)
        # Save first and last name
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        return profile
