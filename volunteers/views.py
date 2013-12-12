# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from volunteers.models import Volunteer

@login_required
def index(request):
    # This one should redirect to the login form if not logged in; otherwise it
    # should display relevant data for the volunteer.
    # return HttpResponse("It works dude!")
    volunteers = Volunteer.objects.order_by('-signed_up')[:5]
    context = {'volunteers': volunteers}
    return render(request, 'volunteers/index.html', context)

@login_required
def volunteer_detail(request, volunteer_id):
    # Where the volunteer can view their own profile.
    volunteer = get_object_or_404(Volunteer, pk=volunteer_id)
    context = {'volunteer': volunteer}
    return render(request, 'volunteers/view.html', context)

@login_required
def volunteer_edit(request, volunteer_id):
    # Where the volunteer can edit their own profile.
    return HttpResponse("You're editing volunteer #%s" % volunteer_id)

def logOut(request):
    logout(request)
    return HttpResponseRedirect('/volunteers/')
