# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, render_to_response,  get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from volunteers.models import Volunteer,  VolunteerTask,  Task
from volunteers.forms import AddTasks

@login_required
def index(request):
    volunteer = Volunteer.objects.filter(user= request.user)
    tasks = VolunteerTask.objects.filter(volunteer=volunteer)
    context = {'tasks': tasks}

    return render(request, 'volunteers/index.html', context)

@login_required
def add_tasks(request):
    if request.method == 'POST':
        form = AddTasks(request.POST)
        #if form.is_valid(): # All validation rules pass
        tasklist = request.POST.getlist('tasks')

        volunteer = Volunteer.objects.get(user= request.user)

        VolunteerTask.objects.filter(volunteer=volunteer.id).delete()

        for task_in in tasklist:
            #current_task = VolunteerTask.objects.get(id=task)
            task = Task.objects.get(id= task_in)
            obj,  volunteer_task = VolunteerTask.objects.get_or_create(task=task,  volunteer=volunteer,
                                                                       defaults={'task': task ,  'volunteer' : volunteer})

        return HttpResponseRedirect('/volunteers/')
    else:
        volunteer = Volunteer.objects.filter(user= request.user)
        add_tasks_form = AddTasks()
        add_tasks_form.fields['tasks'].choices = [(x.id, x) for x in Task.objects.all()]#filter(volunteer=volunteer) ]

        #add_tasks_form.fields['tasks'].initial =  [(x.id, x) for x in VolunteerTask.objects.all()]
        #for task_select in add_tasks_form.fields['tasks'].choices:
        #    task_select.initial = True
        data = {"form":add_tasks_form,}

        return render(request, "volunteers/edit.html", data )

@login_required
def volunteer_edit(request, volunteer_id):
    # Where the volunteer can edit their own profile.
    return HttpResponse("You're editing volunteer #%s" % volunteer_id)

def logOut(request):
    logout(request)
    return HttpResponseRedirect('/volunteers/')
