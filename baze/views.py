from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Darijums
from .forms import DarijumsForm

def index(request):
    darijumi = Darijums.objects.all()
    context = {'darijumi': darijumi}
    return render(request, 'baze/home.html', context)

def addDarijums(request):
    form = DarijumsForm()
    if request.method == 'POST':
        print(request.POST)
        form = DarijumsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')

    context = {'form': form}
    return render(request, 'baze/darijums_add.html', context)
