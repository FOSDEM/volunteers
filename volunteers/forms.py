import random
import string
import re

from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from volunteers.models import Volunteer, VolunteerTask, TaskCategory
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

class EventSignupForm(forms.Form):
    """
    unclear when/whether this is used!
    """
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
            ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]),
            True,
            False
        )
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        return new_user



class SignupForm(forms.ModelForm):
    """
        Form for creating a new user account.

        Validates that the requested username and e-mail is not already in use.
        Also requires the password to be entered twice.
        Requires Privacy policy areement signed by the user.
    """
    USERNAME_RE = r'^[\.\w]+$'
    attrs_dict = {'class': 'required'}

    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Create password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Repeat password"))
    privacy_policy = forms.BooleanField(required=True, label=_("I read and agree to Privacy policy"),
                help_text=_("You must agree to the Privacy policy terms and conditions."),
                                    error_messages={'required': _('You must agree to the Privacy policy terms and conditions.')})

    captcha_answer = forms.CharField(
        required=True,
        label=_("For which word is the D in FOSDEM the abbreviation"),
        help_text=mark_safe("This limits automated signups. Hint: <a href='https://fosdem.org/about/' target='_blank'>about FOSDEM</a>."),
    )

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "username", "email" ]

    def clean_captcha_answer(self):
        value = self.cleaned_data.get("captcha_answer", "").strip().lower()
        if value not in ["developers", "developer", "developers'"]:
            raise forms.ValidationError(_("Incorrect answer. You may find a hint in the about page: https://fosdem.org/about/"))
        return value
    def clean_username(self):
        """
            Validate that the username is alphanumeric and is not already in use.
            Also validates that the username is not listed in
            ``USERENA_FORBIDDEN_USERNAMES`` list.
        """
        username = self.cleaned_data.get('username', '').strip()
        
        # Check if username is empty
        if not username:
            raise forms.ValidationError(_('Username is required.'))
        
        # Validate username format
        if not re.match(self.USERNAME_RE, username):
            raise forms.ValidationError(_('Username can only contain letters, numbers, dots and underscores.'))
        
        # Check for already taken usernames
        try:
            user = get_user_model().objects.get(username__iexact=username)
        except get_user_model().DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_('This username is already taken.'))
        return username

    def clean_email(self):
        """ Validate that the e-mail address is unique. """
        if get_user_model().objects.filter(email__iexact=self.cleaned_data['email']):
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

    def save(self):
        """ Creates a new user and account. Returns the newly created user. """

        first_name, last_name, username, email, password = (self.cleaned_data['first_name'],
                                                            self.cleaned_data['last_name'],
                                                            self.cleaned_data['username'],
                                                            self.cleaned_data['email'],
                                                            self.cleaned_data['password1'])

        new_user = get_user_model().objects.create_user(username, email, password)
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        # Set acceptance timestamp
        if self.cleaned_data.get('privacy_policy'):
            vol = Volunteer.objects.create(user=new_user, privacy_policy_accepted_at=timezone.now(), email_confirmed=False)
            vol.save()

        return new_user

def validate_matrix_id(value):
    matrix_id_pattern = r'^@[a-zA-Z0-9._=-]+:[a-zA-Z0-9.-]+$'
    if not re.match(matrix_id_pattern, value):
        raise ValidationError('Invalid Matrix ID format. The format is @username:homeserver.tld')
class EditProfileForm(forms.ModelForm):
    """ Base form used for fields that are always required """
    first_name = forms.CharField(label=_('First name'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Last name'), max_length=30, required=True)

    def __init__(self, *args, **kw):
        super(EditProfileForm, self).__init__(*args, **kw)
        # Put the first and last name at the top

    class Meta:
        model = Volunteer
        exclude = ['user', 'editions', 'tasks', 'signed_up', 'language', 'privacy', 'private_staff_rating',
                   'private_staff_notes', 'categories']
        fields = ['first_name', 'last_name', 'matrix_id', 'mobile_nbr', 'about_me', 'mugshot']
        help_texts = {
                "mugshot": _("A personal image displayed in your profile. Max 2MB.")
                }

    def clean(self):
        data = super().clean()
        if data.get("matrix_id"):
            validate_matrix_id(data["matrix_id"])
    def save(self, force_insert=False, force_update=False, commit=True):
        profile = super(EditProfileForm, self).save(commit=commit)
        # Save first and last name
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        return profile

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']


class ActivationAwareAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Username or email"),
        widget=forms.TextInput(attrs={"autofocus": True}),
    )


    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            user = authenticate(self.request, username=username_or_email, password=password)

            # If login by username failed, try by email
            if user is None:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(self.request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.fields["username"].label},
                )

            # Activate-based restriction
            self.confirm_login_allowed(user)

            self.user_cache = user

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.volunteer.email_confirmed:
            raise forms.ValidationError(
                _("Your account is not activated yet. Please check your email for the activation link."),
                code='inactive',
            )


class ResendActivationForm(forms.Form):
    email = forms.EmailField(label="Email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        User = get_user_model()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No user with this email exists.")

        if hasattr(user, "volunteer") and user.volunteer.email_confirmed:
            raise forms.ValidationError("This account is already activated.")

        self.user = user
        return email
