from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Avg
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from .models import Darijums, Plans, UserVeikals
from .forms import DarijumsForm, PlansForm
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import plotly.graph_objs as go
from plotly.offline import plot
import calendar

# Funkcija aprēķina atlikušo dienu skaitu mēnesī
def palikusas_dienas(datums_tagad):
    nak_menesis = datums_tagad + relativedelta(months=+1, day=1)
    delta = nak_menesis - datums_tagad
    return delta.days

# Funkcija pieslēgšanās lapai
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Pārbauda vai lietotājs eksistē
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Lietotājs neeksistē')

        user = authenticate(request, username=username, password=password)
        
        # Pieslēdz lietotāju, ja autentifikācija veiksmīga
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Neveiksmīga pieslēgšanās')

    context = {}
    return render(request, 'baze/login_register.html', context)

# Funkcija izlogojo no sistēmas
def logoutUser(request):
    logout(request)
    return redirect('login')

# Galvenā lapa pēc pieslēgšanās
@login_required
def index(request):
    
    user = request.user
    today = date.today()
    menesa_sakums = today + relativedelta(day=1)
    vakardienas_datums = today - timedelta(days=1)

    # Mēģina iegūt lietotāja veikalu
    try:
        user_veikals = UserVeikals.objects.get(user=user).veikals
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav izveidots veikala profils.")
        visi_darijums = Darijums.objects.none()
        visi_summa = {}
        dienas_merkis = {}
        ind_darijumi = Darijums.objects.none()

    # Ja veikals ir pieejams, aprēķina datus, ko parāda mājas lapā
    else:
        visi_darijums = Darijums.objects.filter(lietotajs__userveikals__veikals=user_veikals, datums__date=today)

        # Aprēķina individuālos darījumus priekš individuālās tabulas
        ind_darijumi = visi_darijums.values('lietotajs__username','lietotajs__first_name', 'lietotajs__last_name').annotate(
            kopa_pieslegums=Sum('pieslegums'),
            kopa_atv_iekarta=Sum('atv_iekarta'),
            kopa_nom_iekarta=Sum('nom_iekarta'),
            kopa_pil_iekarta=Sum('pil_iekarta'),
            kopa_viedpaligs=Sum('viedpaligs'),
            kopa_apdr_iekartas=Sum('apdr_iekartas'),
            kopa_aksesuars=Sum('aksesuars'),
            kopa_viedtelevizija=Sum('viedtelevizija')
        )

        # Aprēķina kopējos darījumus priekš kopējās tabulas
        visi_summa = visi_darijums.aggregate(
            kopa_pieslegumi=Sum('pieslegums'),
            kopa_atv_iekarta=Sum('atv_iekarta'),
            kopa_nom_iekarta=Sum('nom_iekarta'),
            kopa_pil_iekarta=Sum('pil_iekarta'),
            kopa_viedpaligs=Sum('viedpaligs'),
            kopa_apdr_iekartas=Sum('apdr_iekartas'),
            kopa_aksesuars=Sum('aksesuars'),
            kopa_viedtelevizija=Sum('viedtelevizija')
        )

        atv = visi_summa.get('kopa_atv_iekarta') or 0
        nom = visi_summa.get('kopa_nom_iekarta') or 0
        pil = visi_summa.get('kopa_pil_iekarta') or 0
        vied = visi_summa.get('kopa_viedpaligs') or 0
        apdr = visi_summa.get('kopa_apdr_iekartas') or 0

        # Aprēķina kopējo iekārtu skaitu
        visi_summa['iekartas_kopa'] = atv + nom + pil

        # Aprēķina atvērto iekārtu proporciju
        if atv + nom != 0:
            visi_summa['atv_proporcija'] = round(atv / (atv + nom), 2) * 100
        else:
            visi_summa['atv_proporcija'] = 0

        # Aprēķina apdrošināto iekārtu proporciju
        if atv + nom + pil + vied !=0:
            visi_summa['apdr_proporcija'] = round(apdr / (atv + nom + pil + vied), 2) * 100
        else:
            visi_summa['apdr_proporcija'] = 0

        # Izfiltrē veikala darījumu mēneša datus priekš dienas mērķa aprēķina
        veikala_darijumi = Darijums.objects.filter(
            lietotajs__userveikals__veikals=user_veikals,
            datums__date__gte=menesa_sakums,
            datums__date__lte=vakardienas_datums,
        )

        if veikala_darijumi.exists():
            veikala_men_summa = veikala_darijumi.aggregate(
                men_pieslegumi=Sum('pieslegums'),
                men_atv_iekarta=Sum('atv_iekarta'),
                men_nom_iekarta=Sum('nom_iekarta'),
                men_pil_iekarta=Sum('pil_iekarta'),
                men_viedpaligs=Sum('viedpaligs'),
                men_apdr_iekartas=Sum('apdr_iekartas'),
                men_aksesuars=Sum('aksesuars'),
                men_viedtelevizija=Sum('viedtelevizija')
            )

            m_atv = veikala_men_summa.get('men_atv_iekarta') or 0
            m_nom = veikala_men_summa.get('men_nom_iekarta') or 0
            m_pil = veikala_men_summa.get('men_pil_iekarta') or 0
            m_vied = veikala_men_summa.get('men_viedpaligs') or 0
            m_apdr = veikala_men_summa.get('men_apdr_iekartas') or 0

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

        # Izfiltrē visus veikala plānus priekš mēneša dienas mērķa aprēķina
        visi_plani = Plans.objects.filter(
            lietotajs__userveikals__veikals=user_veikals,
            menesis=str(today.month),
            gads=today.year
        )

        if visi_plani.exists():
            # Apvieno visus plānus un aprēķina to summas
            plan_sum = visi_plani.aggregate(
                kopa_pieslegumi=Sum('pieslegumi'),
                kopa_iekartas=Sum('iekartas'),
                kopa_viedpaligi=Sum('viedpaligi'),
                kopa_aksesuari=Sum('aksesuari'),
                kopa_viedtelevizija=Sum('viedtelevizija'),
                kopa_apdr_prop = Avg('apdr_proporcija'),
                kopa_atv_prop = Avg('atv_proprocija'),
            )

            # Aprēķina dienas mērķi katrai kategorijai
            dienas_merkis = {
                'pieslegumi': math.ceil(((plan_sum['kopa_pieslegumi'] or 0) - (veikala_men_summa.get('men_pieslegumi') or 0)) / palikusas_dienas(today)),
                'iekartas': math.ceil(((plan_sum['kopa_iekartas'] or 0) - (veikala_men_summa.get('iekartas_kopa') or 0)) / palikusas_dienas(today)),
                'viedpaligi': math.ceil(((plan_sum['kopa_viedpaligi'] or 0) - (veikala_men_summa.get('men_viedpaligs') or 0)) / palikusas_dienas(today)),
                'aksesuari': math.ceil(((plan_sum['kopa_aksesuari'] or 0) - (veikala_men_summa.get('men_aksesuars') or 0)) / palikusas_dienas(today)),
                'atvertais' : round(plan_sum['kopa_atv_prop'] or 0, 1) * 100,
                'apdrosinasana' : round(plan_sum['kopa_apdr_prop'] or 0, 1) * 100,
                'viedtelevizija': math.ceil(((plan_sum['kopa_viedtelevizija'] or 0) - (veikala_men_summa.get('men_viedtelevizija') or 0)) / palikusas_dienas(today)),
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

# Darījumu pievienošanas funkcija
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

# Darījumu rediģēšanas funkcija
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

# Darījumu dzēšanas funkcija
@login_required
def deleteDarijums(request, pk):
    darijums = Darijums.objects.get(id=pk)
    if request.method == "POST":
        darijums.delete()
        return redirect('index')
    return render(request, 'baze/delete.html', {'obj':darijums})

# Plānu lapa ar grafikiem un individuālo progresu
@login_required
def planuLapa(request):
    today = date.today()
    user = request.user
    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        plani = Plans.objects.filter(lietotajs__userveikals__veikals=veikals, menesis=str(today.month), gads=today.year)

        kopa_dienas = calendar.monthrange(today.year, today.month)[1]
        menesa_progress = today.day / kopa_dienas
        paredzetais_progress = menesa_progress * 100
        palikusas_dienas = kopa_dienas - today.day

        grafiki = []
        ind_progresa_dati = None

        # Izveido grafikus katram pārdevējam
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

            kategorijas = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]

            planotais = [
                p.pieslegumi or 0,
                p.iekartas or 0,
                p.viedpaligi or 0,
                p.aksesuari or 0,
                p.viedtelevizija or 0,
            ]
            realais = [
                darijumi["pieslegumi"],
                darijumi["iekartas"],
                darijumi["viedpaligi"],
                darijumi["aksesuari"],
                darijumi["viedtelevizija"],
            ]

            progress = [
                (round(a / b * 100, 1) if b else 0) for a, b in zip(realais, planotais)
            ]

            if p.lietotajs == user:
                ind_progresa_dati = []
                for i, category in enumerate(kategorijas):
                    dienas_merkis = math.ceil((planotais[i] - realais[i]) / palikusas_dienas) if palikusas_dienas > 0 and planotais[i] > realais[i] else 0
                    ind_progresa_dati.append({
                        'kategorija': category,
                        'izpilde': realais[i],
                        'plans': planotais[i],
                        'progress': progress[i],
                        'dienas_merkis': round(dienas_merkis, 2)
                    })

            # Color bars based on progress vs. expected
            colors = ["green" if val >= paredzetais_progress else "red" for val in progress]

            text_labels = [
                f"{a} / {b} ({v:.1f}%)" if b else f"{a} / 0 (0%)"
                for a, b, v in zip(realais, planotais, progress)
            ]

            trace = go.Bar(
                x=kategorijas,
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
                        x1=len(kategorijas),
                        y0=paredzetais_progress,
                        y1=paredzetais_progress,
                        line=dict(color="red", dash="dash"),
                    )
                ],
                annotations=[
                    dict(
                        x=len(kategorijas) - 0.3,
                        y=40,
                        text=f"Paredzētais progress: {paredzetais_progress:.1f}%",
                        textangle=90,
                        showarrow=False,
                        font=dict(color="black"),
                    )
                ],
            )

            fig = go.Figure(data=[trace], layout=layout)
            chart_div = plot(fig, auto_open=False, output_type="div")
            grafiki.append(chart_div)

    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        plani = Plans.objects.none()
        grafiki = []
        ind_progresa_dati = None
        palikusas_dienas = 0

    context = {
        'plani': plani,
        "grafiki": grafiki, 
        'ind_progresa_dati': ind_progresa_dati, 
        'palikusas_dienas': palikusas_dienas
        }
    return render(request, 'baze/plani.html', context)

# Plānu pievienošanas funkcija
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

# Plānu rediģēšanas funkcija
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

# Plānu dzēšanas funkcija
@permission_required('baze.delete_plans', raise_exception=True)
@login_required
def deletePlans(request, pk):
    plans = Plans.objects.get(id=pk)
    if request.method == "POST":
        plans.delete()
        return redirect('plani')
    return render(request, 'baze/delete.html', {'obj':plans})

# Veikala plānu lapa ar kopējo progresu un grafikiem
@login_required
def veikalaPlans(request):
    today = date.today()
    user = request.user
    
    # Iegūst datumu diapazonu no GET parametriem vai izmanto pašreizējo mēnesi un gadu
    sakuma_menesis = request.GET.get('sakuma_menesis', str(today.month))
    sakuma_gads = request.GET.get('sakuma_gads', str(today.year))
    beigu_menesis = request.GET.get('beigu_menesis', str(today.month))
    beigu_gads = request.GET.get('beigu_gads', str(today.year))
    
    try:
        sakuma_menesis = int(sakuma_menesis)
        sakuma_gads = int(sakuma_gads)
        beigu_menesis = int(beigu_menesis)
        beigu_gads = int(beigu_gads)
    except (ValueError, TypeError):
        sakuma_menesis = today.month
        sakuma_gads = today.year
        beigu_menesis = today.month
        beigu_gads = today.year
    
    # izveido datumu objektus no mēnešiem un gadiem
    sakuma_datums = date(sakuma_gads, sakuma_menesis, 1)
    beigu_datums = date(beigu_gads, beigu_menesis, calendar.monthrange(beigu_gads, beigu_menesis)[1])
    
    perioda_kopa_dienas = 0
    elapsed_days_in_period = 0


    patreizejais_datums = sakuma_datums
    while patreizejais_datums <= beigu_datums:
        menesa_dienas = calendar.monthrange(patreizejais_datums.year, patreizejais_datums.month)[1]
        
        if patreizejais_datums.year == today.year and patreizejais_datums.month == today.month:
            # patreizejais_datums month - count only days up to today
            elapsed_days_in_period += today.day
            perioda_kopa_dienas += menesa_dienas
        elif patreizejais_datums < date(today.year, today.month, 1):
            # Past months - count all days as elapsed
            elapsed_days_in_period += menesa_dienas
            perioda_kopa_dienas += menesa_dienas
        else:
            # Future months - count total days but no elapsed days
            perioda_kopa_dienas += menesa_dienas
        
        # Move to next month
        if patreizejais_datums.month == 12:
            patreizejais_datums = date(patreizejais_datums.year + 1, 1, 1)
        else:
            patreizejais_datums = date(patreizejais_datums.year, patreizejais_datums.month + 1, 1)

    # Aprēķina paredzēto progresu procentos
    if perioda_kopa_dienas > 0:
        paredzetais_progress = (elapsed_days_in_period / perioda_kopa_dienas) * 100
    else:
        paredzetais_progress = 0
    
    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        
        # Generate list of months in the date range
        menesi_intervala = []
        patreizejais_datums = sakuma_datums
        while patreizejais_datums <= beigu_datums:
            menesi_intervala.append((patreizejais_datums.month, patreizejais_datums.year))
            # Move to next month
            if patreizejais_datums.month == 12:
                patreizejais_datums = date(patreizejais_datums.year + 1, 1, 1)
            else:
                patreizejais_datums = date(patreizejais_datums.year, patreizejais_datums.month + 1, 1)
        
        veikala_kopa = {
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
        
        # Iegūst plānus un darījumus katram mēnesim un apkopo tos
        for month, year in menesi_intervala:
            plani = Plans.objects.filter(
                lietotajs__userveikals__veikals=veikals, 
                menesis=str(month), 
                gads=year
            )
            

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
                
                veikala_kopa['pieslegumi_plans'] += (p.pieslegumi or 0)
                veikala_kopa['iekartas_plans'] += (p.iekartas or 0)
                veikala_kopa['viedpaligi_plans'] += (p.viedpaligi or 0)
                veikala_kopa['aksesuari_plans'] += (p.aksesuari or 0)
                veikala_kopa['viedtelevizija_plans'] += (p.viedtelevizija or 0)
                
                veikala_kopa['pieslegumi_izpilde'] += (darijumi['pieslegumi'] or 0)
                veikala_kopa['iekartas_izpilde'] += (darijumi['iekartas'] or 0)
                veikala_kopa['viedpaligi_izpilde'] += (darijumi['viedpaligi'] or 0)
                veikala_kopa['aksesuari_izpilde'] += (darijumi['aksesuari'] or 0)
                veikala_kopa['viedtelevizija_izpilde'] += (darijumi['viedtelevizija'] or 0)
        
        kategorijas = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]
        kategoriju_atslegas = ['pieslegumi', 'iekartas', 'viedpaligi', 'aksesuari', 'viedtelevizija']
        
        tabulas_dati = []
        planotais = []
        realais = []
        progress = []
        
        for i, category in enumerate(kategorijas):
            key = kategoriju_atslegas[i]
            plans_val = veikala_kopa[f'{key}_plans']
            izpilde_val = veikala_kopa[f'{key}_izpilde']
            progress_val = round(izpilde_val / plans_val * 100, 1) if plans_val else 0
            
            tabulas_dati.append({
                'kategorija': category,
                'izpilde': izpilde_val,
                'plans': plans_val,
                'progress': progress_val
            })
            
            planotais.append(plans_val)
            realais.append(izpilde_val)
            progress.append(progress_val)
        
        colors = ["green" if val >= paredzetais_progress else "red" for val in progress]
        
        text_labels = [
            f"{a} / {b} ({v:.1f}%)" if b else f"{a} / 0 (0%)"
            for a, b, v in zip(realais, planotais, progress)
        ]
        
        trace = go.Bar(
            x=kategorijas,
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
        
        # Izveido perioda tekstu virsrakstam
        if sakuma_menesis == beigu_menesis and sakuma_gads == beigu_gads:
            period_text = f"{menesi_latviski[sakuma_menesis]} {sakuma_gads}"
        else:
            period_text = f"{menesi_latviski[sakuma_menesis]} {sakuma_gads} - {menesi_latviski[beigu_menesis]} {beigu_gads}"
        
        layout = go.Layout(
            title=f"{veikals.nosaukums} — progress ({period_text})",
            yaxis=dict(title="Izpilde (%)", range=[0, 120]),
            title_x=0.5,
            shapes=[
                dict(
                    type="line",
                    x0=-0.5,
                    x1=len(kategorijas),
                    y0=paredzetais_progress,
                    y1=paredzetais_progress,
                    line=dict(color="red", dash="dash"),
                )
            ],
            annotations=[
                dict(
                    x=len(kategorijas) - 0.3,
                    y=40,
                    text=f"Paredzētais progress: {paredzetais_progress:.1f}%",
                    textangle=90,
                    showarrow=False,
                    font=dict(color="black"),
                )
            ],
        )
        
        fig = go.Figure(data=[trace], layout=layout)
        chart_div = plot(fig, auto_open=False, output_type="div")
        
        # Ģenerē gadu un mēnešu sarakstu izvēlnēm
        patreizejais_datums_year = today.year
        years = list(range(patreizejais_datums_year - 2, patreizejais_datums_year + 1))  # 2 years before and after
        months = [
            (1, 'Janvāris'), (2, 'Februāris'), (3, 'Marts'), (4, 'Aprīlis'),
            (5, 'Maijs'), (6, 'Jūnijs'), (7, 'Jūlijs'), (8, 'Augusts'),
            (9, 'Septembris'), (10, 'Oktobris'), (11, 'Novembris'), (12, 'Decembris')
        ]
        
        context = {
            'veikals': veikals,
            'tabulas_dati': tabulas_dati,
            'chart': chart_div,
            'paredzetais_progress': round(paredzetais_progress, 1),
            'period_text': period_text,
            'sakuma_menesis': sakuma_menesis,
            'sakuma_gads': sakuma_gads,
            'beigu_menesis': beigu_menesis,
            'beigu_gads': beigu_gads,
            'months': months,
            'years': years,
        }
        
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        
        patreizejais_datums_year = today.year
        years = list(range(patreizejais_datums_year - 2, patreizejais_datums_year + 2))
        months = [
            (1, 'Janvāris'), (2, 'Februāris'), (3, 'Marts'), (4, 'Aprīlis'),
            (5, 'Maijs'), (6, 'Jūnijs'), (7, 'Jūlijs'), (8, 'Augusts'),
            (9, 'Septembris'), (10, 'Oktobris'), (11, 'Novembris'), (12, 'Decembris')
        ]
        
        context = {
            'veikals': None,
            'tabulas_dati': [],
            'chart': None,
            'paredzetais_progress': 0,
            'sakuma_menesis': today.month,
            'sakuma_gads': today.year,
            'beigu_menesis': today.month,
            'beigu_gads': today.year,
            'months': months,
            'years': years,
        }
    
    return render(request, 'baze/veikala_plans.html', context)