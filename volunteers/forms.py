from django import forms
from volunteers.models import VolunteerTask
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.admin import widgets

class AddTasks(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=VolunteerTask.objects.none(), widget=forms.CheckboxSelectMultiple())
