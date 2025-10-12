from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Darijums
from .forms import DarijumsForm



def loginPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Lietotājs neeksistē')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Neveiksmīga pieslēgšanās')
            
    context = {}
    return render(request, 'baze/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('index')

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

def editDarijums(request, pk):
    darijums = Darijums.objects.get(id=pk)
    form = DarijumsForm(instance=darijums)

    if request.method == 'POST':
        form = DarijumsForm(request.POST, instance=darijums)
        if form.is_valid():
            form.save()
            return redirect('index')

    context = {'form' : form}
    return render(request, 'baze/darijums_add.html', context)

def deleteDarijums(request, pk):
    darijums = Darijums.objects.get(id=pk)
    if request.method == "POST":
        darijums.delete()
        return redirect('index')
    return render(request, 'baze/delete.html', {'obj':darijums})