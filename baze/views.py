from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Avg, F
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from .models import Darijums, Plans, UserVeikals
from .forms import DarijumsForm, PlansForm
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math


def palikusas_dienas(current_date):
    next_month = current_date + relativedelta(months=+1, day=1)
    delta = next_month - current_date
    return delta.days

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
    today = date.today()
    start_of_month = today + relativedelta(day=1)
    vakardienas_datums = today - timedelta(days=1)

    try:
        user_veikals = UserVeikals.objects.get(user=user).veikals
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav izveidots veikala profils.")
        visi_darijums = Darijums.objects.none()
        visi_summa = {}
        dienas_merkis = {}
    else:
        visi_darijums = Darijums.objects.filter(lietotajs__userveikals__veikals=user_veikals, datums__date=today)

        ind_darijumi = visi_darijums.values('lietotajs__username','lietotajs__first_name', 'lietotajs__last_name').annotate(
            total_pieslegums=Sum('pieslegums'),
            total_atv_iekarta=Sum('atv_iekarta'),
            total_nom_iekarta=Sum('nom_iekarta'),
            total_pil_iekarta=Sum('pil_iekarta'),
            total_viedpaligs=Sum('viedpaligs'),
            total_apdr_iekartas=Sum('apdr_iekartas'),
            total_aksesuars=Sum('aksesuars'),
            total_viedtelevizija=Sum('viedtelevizija')
        )

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

        if atv + nom != 0:
            visi_summa['atv_proporcija'] = round(atv / (atv + nom), 2) * 100
        else:
            visi_summa['atv_proporcija'] = 0

        if atv + nom + pil + vied !=0:
            visi_summa['apdr_proporcija'] = round(apdr / (atv + nom + pil + vied), 2) * 100
        else:
            visi_summa['apdr_proporcija'] = 0


        veikala_darijumi = Darijums.objects.filter(
            lietotajs__userveikals__veikals=user_veikals,
            datums__date__gte=start_of_month,
            datums__date__lte=vakardienas_datums,
        )

        if veikala_darijumi.exists():
            veikala_men_summa = veikala_darijumi.aggregate(
                men_pieslegumi=Sum('pieslegums'),
                total_atv_iekarta=Sum('atv_iekarta'),
                total_nom_iekarta=Sum('nom_iekarta'),
                total_pil_iekarta=Sum('pil_iekarta'),
                total_viedpaligs=Sum('viedpaligs'),
                total_apdr_iekartas=Sum('apdr_iekartas'),
                total_aksesuars=Sum('aksesuars'),
                total_viedtelevizija=Sum('viedtelevizija')
            )

            m_atv = veikala_men_summa.get('total_atv_iekarta') or 0
            m_nom = veikala_men_summa.get('total_nom_iekarta') or 0
            m_pil = veikala_men_summa.get('total_pil_iekarta') or 0
            m_vied = veikala_men_summa.get('total_viedpaligs') or 0
            m_apdr = veikala_men_summa.get('total_apdr_iekartas') or 0

            veikala_men_summa['iekartas_kopa'] = m_atv + m_nom + m_pil

            if m_atv + m_nom != 0:
                veikala_men_summa['atv_proporcija'] = round(m_atv / (m_atv + m_nom), 3) * 100
            else:
                veikala_men_summa['atv_proporcija'] = 0

            if m_atv + m_nom + m_pil + m_vied !=0:
                veikala_men_summa['apdr_proporcija'] = round(m_apdr / (atv + m_nom + m_pil + m_vied), 3) * 100
            else:
                veikala_men_summa['apdr_proporcija'] = 0

        else:
            veikala_men_summa = {}

        visi_plani = Plans.objects.filter(
            lietotajs__userveikals__veikals=user_veikals,
            menesis=str(today.month),
            gads=today.year
        )

        if visi_plani.exists():
            plan_sum = visi_plani.aggregate(
                total_pieslegumi=Sum('pieslegumi'),
                total_iekartas=Sum('iekartas'),
                total_viedpaligi=Sum('viedpaligi'),
                total_aksesuari=Sum('aksesuari'),
                total_viedtelevizija=Sum('viedtelevizija'),
                total_apdr_prop = Avg('apdr_proporcija'),
                total_atv_prop = Avg('atv_proprocija'),
            )

            dienas_merkis = {
                'pieslegumi': math.ceil(((plan_sum['total_pieslegumi'] or 0) - (veikala_men_summa.get('men_pieslegumi') or 0)) / palikusas_dienas(today)),
                'iekartas': math.ceil(((plan_sum['total_iekartas'] or 0) - (veikala_men_summa.get('iekartas_kopa') or 0)) / palikusas_dienas(today)),
                'viedpaligi': math.ceil(((plan_sum['total_viedpaligi'] or 0) - (veikala_men_summa.get('total_viedpaligs') or 0)) / palikusas_dienas(today)),
                'aksesuari': math.ceil(((plan_sum['total_aksesuari'] or 0) - (veikala_men_summa.get('total_aksesuars') or 0)) / palikusas_dienas(today)),
                'atvertais' : round(plan_sum['total_atv_prop'] or 0, 1) * 100,
                'apdrosinasana' : round(plan_sum['total_apdr_prop'] or 0, 1) * 100,
                'viedtelevizija': math.ceil(((plan_sum['total_viedtelevizija'] or 0) - (veikala_men_summa.get('total_viedtelevizija') or 0)) / palikusas_dienas(today)),
            }
        else:
            dienas_merkis = {}


        


    darijumi = Darijums.objects.filter(lietotajs=request.user, datums__date=today)
    context = {'darijumi': darijumi, 'visi_darijumi':visi_darijums,'visi_summa': visi_summa, 'dienas_merkis': dienas_merkis, 'ind_darijumi': ind_darijumi}
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