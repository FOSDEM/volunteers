from volunteers.models import VolunteerTask, TaskCategory, Edition, Task

from django import forms
from django.contrib.admin import widgets
from django.utils.translation import ugettext as _
from django.forms.extras.widgets import SelectDateWidget

from userena.utils import get_profile_model

class AddTasksForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=VolunteerTask.objects.none(), widget=forms.CheckboxSelectMultiple())

class EditTasksForm(forms.Form):
    #do = forms.BooleanField(label=_(u'Do'), required=False)
    #nbr_volunteers = forms.IntegerField(label=_(u'Assigned volunteers'), required=True)
    date = forms.TimeField(label=_(u'Date'), required=True)
    start_time = forms.TimeField(label=_(u'Start time'), required=True)
    end_time = forms.TimeField(label=_(u'End time'), required=True)
    name = forms.CharField(label=_(u'Name'), max_length=30, required=True)
    description = forms.CharField(label=_(u'Description'), max_length=30, required=False, widget=forms.Textarea)

class EditProfileForm(forms.ModelForm):
    """ Base form used for fields that are always required """
    first_name = forms.CharField(label=_(u'First name'), max_length=30, required=False)
    last_name = forms.CharField(label=_(u'Last name'), max_length=30, required=False)

    categories = forms.ModelMultipleChoiceField(label=_(u'Categories'), queryset=TaskCategory.objects.all(), widget=forms.CheckboxSelectMultiple(), required=False)

    def __init__(self, *args, **kw):
        super(EditProfileForm, self).__init__(*args, **kw)
        # Put the first and last name at the top
        new_order = self.fields.keyOrder[:-2]
        new_order.insert(0, 'first_name')
        new_order.insert(1, 'last_name')
        self.fields.keyOrder = new_order

    class Meta:
        model = get_profile_model()
        exclude = ['user', 'editions', 'tasks']

    def save(self, force_insert=False, force_update=False, commit=True):
        profile = super(EditProfileForm, self).save(commit=commit)
        # Save first and last name
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        return profile