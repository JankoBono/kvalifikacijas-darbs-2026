from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import Sum, Avg
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.functions import Coalesce
from .models import Darijums, Plans, UserVeikals
from .forms import DarijumsForm, PlansForm
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import plotly.graph_objs as go
from plotly.offline import plot
import calendar


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
        ind_darijumi = Darijums.objects.none()
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
    context = {
        'darijumi': darijumi, 
        'visi_darijumi':visi_darijums,
        'visi_summa': visi_summa, 
        'dienas_merkis': dienas_merkis, 
        'ind_darijumi': ind_darijumi
        }
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
    today = date.today()
    user = request.user
    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        plani = Plans.objects.filter(lietotajs__userveikals__veikals=veikals, menesis=str(today.month), gads=today.year)

        total_days = calendar.monthrange(today.year, today.month)[1]
        month_progress = today.day / total_days
        expected_progress = month_progress * 100
        remaining_days = total_days - today.day

        charts = []
        user_progress_data = None

        for p in plani:
            darijumi = Darijums.objects.filter(
                lietotajs=p.lietotajs,
                datums__month=today.month,
                datums__year=today.year,
            ).aggregate(
                pieslegumi=Sum('pieslegums') or 0,
                iekartas=Sum('atv_iekarta') + Sum('nom_iekarta') + Sum('pil_iekarta'),
                viedpaligi=Sum('viedpaligs') or 0,
                aksesuari=Sum('aksesuars') or 0,
                viedtelevizija=Sum('viedtelevizija') or 0,
            )

            for key, val in darijumi.items():
                darijumi[key] = val or 0

            categories = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]

            planned = [
                p.pieslegumi or 0,
                p.iekartas or 0,
                p.viedpaligi or 0,
                p.aksesuari or 0,
                p.viedtelevizija or 0,
            ]
            actual = [
                darijumi["pieslegumi"],
                darijumi["iekartas"],
                darijumi["viedpaligi"],
                darijumi["aksesuari"],
                darijumi["viedtelevizija"],
            ]

            progress = [
                (round(a / b * 100, 1) if b else 0) for a, b in zip(actual, planned)
            ]

            if p.lietotajs == user:
                user_progress_data = []
                for i, category in enumerate(categories):
                    daily_target = math.ceil((planned[i] - actual[i]) / remaining_days) if remaining_days > 0 and planned[i] > actual[i] else 0
                    user_progress_data.append({
                        'kategorija': category,
                        'izpilde': actual[i],
                        'plans': planned[i],
                        'progress': progress[i],
                        'daily_target': round(daily_target, 2)
                    })

            # Color bars based on progress vs. expected
            colors = ["green" if val >= expected_progress else "red" for val in progress]

            text_labels = [
                f"{a} / {b} ({v:.1f}%)" if b else f"{a} / 0 (0%)"
                for a, b, v in zip(actual, planned, progress)
            ]

            trace = go.Bar(
                x=categories,
                y=progress,
                marker_color=colors,
                text=text_labels,
                textposition="auto",
            )

            layout = go.Layout(
                title=f"{p.lietotajs.first_name} {p.lietotajs.last_name or p.lietotajs.username} — mēneša progress",
                yaxis=dict(title="Izpilde (%)", range=[0, 120]),
                title_x=0.5,
                shapes=[
                    dict(
                        type="line",
                        x0=-0.5,
                        x1=len(categories),
                        y0=expected_progress,
                        y1=expected_progress,
                        line=dict(color="red", dash="dash"),
                    )
                ],
                annotations=[
                    dict(
                        x=len(categories) - 0.3,
                        y=40,
                        text=f"Paredzētais progress: {expected_progress:.1f}%",
                        textangle=90,
                        showarrow=False,
                        font=dict(color="black"),
                    )
                ],
            )

            fig = go.Figure(data=[trace], layout=layout)
            chart_div = plot(fig, auto_open=False, output_type="div")
            charts.append(chart_div)

    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        plani = Plans.objects.none()
        charts = []
        user_progress_data = None
        remaining_days = 0

    context = {
        'plani': plani,
        "charts": charts, 
        'user_progress_data': user_progress_data, 
        'remaining_days': remaining_days
        }
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
            
            plan.save()
            messages.success(request, "Plāns veiksmīgi pievienots!")
            return redirect('plani')
        else:
            # Check if the error is due to unique constraint
            if '__all__' in form.errors:
                for error in form.errors['__all__']:
                    if 'already exists' in str(error):
                        messages.error(request, "Šim lietotājam jau ir izveidots plāns šim mēnesim un gadam.")
                        # Clear the default error message
                        form.errors['__all__'].clear()
                        break

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

@login_required
def veikalaPlans(request):
    today = date.today()
    user = request.user
    
    # Get date range from request, default to current month
    start_month = request.GET.get('start_month', str(today.month))
    start_year = request.GET.get('start_year', str(today.year))
    end_month = request.GET.get('end_month', str(today.month))
    end_year = request.GET.get('end_year', str(today.year))
    
    try:
        start_month = int(start_month)
        start_year = int(start_year)
        end_month = int(end_month)
        end_year = int(end_year)
    except (ValueError, TypeError):
        start_month = today.month
        start_year = today.year
        end_month = today.month
        end_year = today.year
    
    # Create start and end dates
    start_date = date(start_year, start_month, 1)
    end_date = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
    
    # Calculate expected progress based on date range
    # Count total days and elapsed days in the period
    total_days_in_period = 0
    elapsed_days_in_period = 0

    # Generate list of months in the date range for progress calculation
    current = start_date
    while current <= end_date:
        days_in_month = calendar.monthrange(current.year, current.month)[1]
        
        if current.year == today.year and current.month == today.month:
            # Current month - count only days up to today
            elapsed_days_in_period += today.day
            total_days_in_period += days_in_month
        elif current < date(today.year, today.month, 1):
            # Past months - count all days as elapsed
            elapsed_days_in_period += days_in_month
            total_days_in_period += days_in_month
        else:
            # Future months - count total days but no elapsed days
            total_days_in_period += days_in_month
        
        # Move to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    # Calculate expected progress percentage
    if total_days_in_period > 0:
        expected_progress = (elapsed_days_in_period / total_days_in_period) * 100
    else:
        expected_progress = 0
    
    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        
        # Generate list of months in the date range
        months_in_range = []
        current = start_date
        while current <= end_date:
            months_in_range.append((current.month, current.year))
            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        # Initialize totals
        store_totals = {
            'pieslegumi_plans': 0,
            'pieslegumi_izpilde': 0,
            'iekartas_plans': 0,
            'iekartas_izpilde': 0,
            'viedpaligi_plans': 0,
            'viedpaligi_izpilde': 0,
            'aksesuari_plans': 0,
            'aksesuari_izpilde': 0,
            'viedtelevizija_plans': 0,
            'viedtelevizija_izpilde': 0,
        }
        
        # Get all plans for this store for the selected period
        for month, year in months_in_range:
            plani = Plans.objects.filter(
                lietotajs__userveikals__veikals=veikals, 
                menesis=str(month), 
                gads=year
            )
            
            # Sum up all plans and actual results for the store
            for p in plani:
                darijumi = Darijums.objects.filter(
                    lietotajs=p.lietotajs,
                    datums__month=month,
                    datums__year=year,
                ).aggregate(
                    pieslegumi=Sum('pieslegums') or 0,
                    iekartas=Sum('atv_iekarta') + Sum('nom_iekarta') + Sum('pil_iekarta'),
                    viedpaligi=Sum('viedpaligs') or 0,
                    aksesuari=Sum('aksesuars') or 0,
                    viedtelevizija=Sum('viedtelevizija') or 0,
                )
                
                # Sum plans
                store_totals['pieslegumi_plans'] += (p.pieslegumi or 0)
                store_totals['iekartas_plans'] += (p.iekartas or 0)
                store_totals['viedpaligi_plans'] += (p.viedpaligi or 0)
                store_totals['aksesuari_plans'] += (p.aksesuari or 0)
                store_totals['viedtelevizija_plans'] += (p.viedtelevizija or 0)
                
                # Sum actual results
                store_totals['pieslegumi_izpilde'] += (darijumi['pieslegumi'] or 0)
                store_totals['iekartas_izpilde'] += (darijumi['iekartas'] or 0)
                store_totals['viedpaligi_izpilde'] += (darijumi['viedpaligi'] or 0)
                store_totals['aksesuari_izpilde'] += (darijumi['aksesuari'] or 0)
                store_totals['viedtelevizija_izpilde'] += (darijumi['viedtelevizija'] or 0)
        
        # Prepare data for table
        categories = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]
        category_keys = ['pieslegumi', 'iekartas', 'viedpaligi', 'aksesuari', 'viedtelevizija']
        
        table_data = []
        planned = []
        actual = []
        progress = []
        
        for i, category in enumerate(categories):
            key = category_keys[i]
            plans_val = store_totals[f'{key}_plans']
            izpilde_val = store_totals[f'{key}_izpilde']
            progress_val = round(izpilde_val / plans_val * 100, 1) if plans_val else 0
            
            table_data.append({
                'kategorija': category,
                'izpilde': izpilde_val,
                'plans': plans_val,
                'progress': progress_val
            })
            
            planned.append(plans_val)
            actual.append(izpilde_val)
            progress.append(progress_val)
        
        # Create chart
        colors = ["green" if val >= expected_progress else "red" for val in progress]
        
        text_labels = [
            f"{a} / {b} ({v:.1f}%)" if b else f"{a} / 0 (0%)"
            for a, b, v in zip(actual, planned, progress)
        ]
        
        trace = go.Bar(
            x=categories,
            y=progress,
            marker_color=colors,
            text=text_labels,
            textposition="auto",
        )

        menesi_latviski = {
            1: 'Janvāris', 2: 'Februāris', 3: 'Marts', 4: 'Aprīlis',
            5: 'Maijs', 6: 'Jūnijs', 7: 'Jūlijs', 8: 'Augusts',
            9: 'Septembris', 10: 'Oktobris', 11: 'Novembris', 12: 'Decembris'
        }
        
        # Create period description
        if start_month == end_month and start_year == end_year:
            period_text = f"{menesi_latviski[start_month]} {start_year}"
        else:
            period_text = f"{menesi_latviski[start_month]} {start_year} - {menesi_latviski[end_month]} {end_year}"
        
        layout = go.Layout(
            title=f"{veikals.nosaukums} — progress ({period_text})",
            yaxis=dict(title="Izpilde (%)", range=[0, 120]),
            title_x=0.5,
            shapes=[
                dict(
                    type="line",
                    x0=-0.5,
                    x1=len(categories),
                    y0=expected_progress,
                    y1=expected_progress,
                    line=dict(color="red", dash="dash"),
                )
            ],
            annotations=[
                dict(
                    x=len(categories) - 0.3,
                    y=40,
                    text=f"Paredzētais progress: {expected_progress:.1f}%",
                    textangle=90,
                    showarrow=False,
                    font=dict(color="black"),
                )
            ],
        )
        
        fig = go.Figure(data=[trace], layout=layout)
        chart_div = plot(fig, auto_open=False, output_type="div")
        
        # Generate month and year options for dropdowns
        current_year = today.year
        years = list(range(current_year - 2, current_year + 1))  # 2 years before and after
        months = [
            (1, 'Janvāris'), (2, 'Februāris'), (3, 'Marts'), (4, 'Aprīlis'),
            (5, 'Maijs'), (6, 'Jūnijs'), (7, 'Jūlijs'), (8, 'Augusts'),
            (9, 'Septembris'), (10, 'Oktobris'), (11, 'Novembris'), (12, 'Decembris')
        ]
        
        context = {
            'veikals': veikals,
            'table_data': table_data,
            'chart': chart_div,
            'expected_progress': round(expected_progress, 1),
            'period_text': period_text,
            'start_month': start_month,
            'start_year': start_year,
            'end_month': end_month,
            'end_year': end_year,
            'months': months,
            'years': years,
        }
        
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        
        current_year = today.year
        years = list(range(current_year - 2, current_year + 2))
        months = [
            (1, 'Janvāris'), (2, 'Februāris'), (3, 'Marts'), (4, 'Aprīlis'),
            (5, 'Maijs'), (6, 'Jūnijs'), (7, 'Jūlijs'), (8, 'Augusts'),
            (9, 'Septembris'), (10, 'Oktobris'), (11, 'Novembris'), (12, 'Decembris')
        ]
        
        context = {
            'veikals': None,
            'table_data': [],
            'chart': None,
            'expected_progress': 0,
            'start_month': today.month,
            'start_year': today.year,
            'end_month': today.month,
            'end_year': today.year,
            'months': months,
            'years': years,
        }
    
    return render(request, 'baze/veikala_plans.html', context)