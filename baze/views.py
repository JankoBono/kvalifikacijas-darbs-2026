from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from .models import Darijums, Plans, UserVeikals
from .forms import DarijumsForm, PlansForm



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
    return redirect('login')

@login_required
def index(request):
    
    user = request.user

    try:
        user_veikals = UserVeikals.objects.get(user=user).veikals
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav izveidots veikala profils.")
        visi_darijums = Darijums.objects.none()
        visi_summa = {}
    else:
        visi_darijums = Darijums.objects.filter(lietotajs__userveikals__veikals=user_veikals)
        visi_summa = visi_darijums.aggregate(
            total_pieslegumi=Sum('pieslegums'),
            total_atv_iekarta=Sum('atv_iekarta'),
            total_nom_iekarta=Sum('nom_iekarta'),
            total_pil_iekarta=Sum('pil_iekarta'),
            total_viedpaligs=Sum('viedpaligs'),
            total_apdr_iekartas=Sum('apdr_iekartas'),
            total_aksesuars=Sum('aksesuars'),
            total_viedtelevizija=Sum('viedtelevizija')
        )

        atv = visi_summa.get('total_atv_iekarta') or 0
        nom = visi_summa.get('total_nom_iekarta') or 0
        pil = visi_summa.get('total_pil_iekarta') or 0
        vied = visi_summa.get('total_viedpaligs') or 0
        apdr = visi_summa.get('total_apdr_iekartas') or 0

        visi_summa['iekartas_kopa'] = atv + nom + pil

        visi_summa['atv_proporcija'] = round(atv / (atv + nom), 3) * 100
        visi_summa['apdr_proporcija'] = round(apdr / (atv + nom + pil + vied), 3) * 100

    darijumi = Darijums.objects.filter(lietotajs=request.user)
    context = {'darijumi': darijumi, 'visi_darijumi':visi_darijums,'visi_summa': visi_summa}
    return render(request, 'baze/home.html', context)

@login_required
def addDarijums(request):
    form = DarijumsForm()
    if request.method == 'POST':
        print(request.POST)
        form = DarijumsForm(request.POST)
        if form.is_valid():
            darijums_instance = form.save(commit=False)
            darijums_instance.lietotajs = request.user
            darijums_instance.save()
            return redirect('index')

    context = {'form': form}
    return render(request, 'baze/darijums_add.html', context)

@login_required
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

@login_required
def deleteDarijums(request, pk):
    darijums = Darijums.objects.get(id=pk)
    if request.method == "POST":
        darijums.delete()
        return redirect('index')
    return render(request, 'baze/delete.html', {'obj':darijums})

@login_required
def planuLapa(request):
    user = request.user
    try:
            user_veikals = UserVeikals.objects.get(user=user)
            veikals = user_veikals.veikals

            plani = Plans.objects.filter(lietotajs__userveikals__veikals=veikals)
    
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        plani = Plans.objects.none()

    context = {'plani': plani}
    return render(request, 'baze/plani.html', context)

@permission_required('baze.add_plans', raise_exception=True)
@login_required
def addPlans(request):
    form = PlansForm(user=request.user)
    if request.method == 'POST':
        print(request.POST)
        form = PlansForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            try:
                plan.save()
                messages.success(request, "Plāns veiksmīgi pievienots!")
                return redirect('plani')
            except IntegrityError:
                messages.error(request, "Šim lietotājam jau ir izveidots plāns šim mēnesim un gadam.")

    context = {'form': form}
    return render(request, 'baze/plans_add.html', context)

@permission_required('baze.change_plans', raise_exception=True)
@login_required
def editPlans(request, pk):
    plans = Plans.objects.get(id=pk)
    form = PlansForm(instance=plans, user=request.user)

    if request.method == 'POST':
        form = PlansForm(request.POST, instance=plans, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            form.save()
            return redirect('plani')

    context = {'form' : form}
    return render(request, 'baze/plans_add.html', context)

@permission_required('baze.delete_plans', raise_exception=True)
@login_required
def deletePlans(request, pk):
    plans = Plans.objects.get(id=pk)
    if request.method == "POST":
        plans.delete()
        return redirect('plani')
    return render(request, 'baze/delete.html', {'obj':plans})