from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import Darijums, Plans, UserVeikals, Menesis
from .utils import aprekina_veikala_dienas_datus, apreikina_paredzeto_progresu, aprekina_menesus_intervala, veido_grafiku, aprekina_ind_lig_proporcijas, aprekina_ind_darijumus, individualie_dati, aprekina_veikala_datus, veikala_grafika_dati, izveido_perioda_tekstu
from .forms import DarijumsForm, PlansForm
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar

def loginPage(request):
    """"
    Lietotāja pieslēgšanās funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar pieslēgšanās lapu vai pāradresāciju uz galveno lapu pēc veiksmīgas pieslēgšanās
    """
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

def logoutUser(request):
    """"
    Lietotāja izlogošana no sistēmas.

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar pāradresāciju uz pieslēgšanās lapu
    """
    logout(request)
    return redirect('login')

@login_required
def index(request):
    """
    Galvenā lapa pēc lietotāja pieslēgšanās, kur tiek rādīti veikala dati un individuālie darījumi.

    Argumenti:
        request: HTTP pieprasījuma objekts
    
    Atgriež:
        HTTP atbildes objektu ar galveno lapu un kontekstu
    """
    try:
        lietotaja_veikals = UserVeikals.objects.get(user=request.user).veikals

        # Iegūst veikala dienas datus
        veikala_dati = aprekina_veikala_dienas_datus(lietotaja_veikals)

        # Aprēķina individuālos darījumus priekš katra kolēģa individuālās tabulas
        ind_darijumi = aprekina_ind_darijumus(lietotaja_veikals)
        
        context = {
            'visi_summa': veikala_dati['visi_summa'],
            'dienas_merkis': veikala_dati['dienas_merkis'],
            'ind_darijumi': ind_darijumi
        }
        
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        context = {
            'visi_summa': {},
            'dienas_merkis': {},
            'ind_darijumi': [],
        }
    
    return render(request, 'baze/home.html', context)

@login_required
def addDarijums(request):
    """
    Lietotāja darījumu pievienošanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts
    
    Atgriež:
        HTTP atbildes objektu ar darījumu pievienošanas lapu vai pāradresāciju uz galveno lapu pēc veiksmīgas darījuma pievienošanas
    """
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
    """
    Lietotāja darījumu rediģēšanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts
        pk: Darījuma primārā atslēga (ID)

    Atgriež:
        HTTP atbildes objektu ar darījumu rediģēšanas lapu vai pāradresāciju uz darījumu sarakstu pēc veiksmīgas darījuma rediģēšanas
    """
    darijums = Darijums.objects.get(id=pk)
    form = DarijumsForm(instance=darijums)

    if request.method == 'POST':
        form = DarijumsForm(request.POST, instance=darijums)
        if form.is_valid():
            form.save()
            return redirect('mani-darijumi')

    context = {'form' : form}
    return render(request, 'baze/darijums_add.html', context)

@login_required
@require_POST
def deleteDarijums(request, pk):
    """
    Lietotāja darījumu dzēšanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts
        pk: Darījuma primārā atslēga (ID)

    Atgriež:
        HTTP atbildes objektu ar pāradresāciju uz darījumu sarakstu pēc veiksmīgas darījuma dzēšanas
    """

    try:
        darijums = Darijums.objects.get(id=pk)
        
        darijums.delete()
        messages.success(request, "Darījums veiksmīgi izdzēsts!")

    except Darijums.DoesNotExist:
        messages.error(request, "Darījums nav atrasts.")

    return redirect('mani-darijumi')

@login_required
def maniDarijumi(request):
    """
    Lietotāja individuālo darījumu saraksta lapa.

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar darījumu saraksta lapu un kontekstu
    """
    user = request.user
    today = date.today()
    menesa_sakums = today + relativedelta(day=1)

    darijumi = Darijums.objects.filter(
            lietotajs=user,
            datums__date__gte=menesa_sakums,
            datums__date__lte=today,
        ).order_by('-datums')

    context = {'darijumi': darijumi}
    return render(request, 'baze/mani_darijumi.html', context)

@login_required
def planuLapa(request):
    """
    Veikala plānu lapa ar kopējo progresu un grafikiem. 

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar plānu lapu un kontekstu
    """
    today = date.today()
    user = request.user
    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        plani = Plans.objects.filter(
            lietotajs__userveikals__veikals=veikals,
            menesis__menesis_id=today.month,
            gads=today.year
        )

        kopa_dienas = calendar.monthrange(today.year, today.month)[1]
        paredzetais_progress = (today.day / kopa_dienas) * 100
        palikusas_dienas = kopa_dienas - today.day

        proporcijas = aprekina_ind_lig_proporcijas(user)

        ind_progresa_dati, grafiki = individualie_dati(plani, palikusas_dienas, paredzetais_progress, user) 

    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        plani = Plans.objects.none()
        grafiki = []
        ind_progresa_dati = []
        palikusas_dienas = 0

    context = {
        'plani': plani,
        'grafiki': grafiki, 
        'ind_progresa_dati': ind_progresa_dati, 
        'palikusas_dienas': palikusas_dienas,
        'proporcijas': proporcijas,
        }
    return render(request, 'baze/plani.html', context)

@permission_required('baze.add_plans', raise_exception=True)
@login_required
def addPlans(request):
    """
    Veikala plānu pievienošanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar plānu pievienošanas lapu vai pāradresāciju uz plānu sarakstu pēc veiksmīgas plāna pievienošanas
    """
    form = PlansForm(user=request.user)
    if request.method == 'POST':
        print(request.POST)
        form = PlansForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.save()
            messages.success(request, "Plāns veiksmīgi pievienots!")
            return redirect('plani')

    context = {'form': form}
    return render(request, 'baze/plans_add.html', context)

@permission_required('baze.change_plans', raise_exception=True)
@login_required
def editPlans(request, pk):
    """
    Veikala plānu rediģēšanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts
        pk: Plāna primārā atslēga (ID)

    Atgriež:
        HTTP atbildes objektu ar plānu rediģēšanas lapu vai pāradresāciju uz plānu sarakstu pēc veiksmīgas plāna rediģēšanas
    """
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
    """
    Veikala plānu dzēšanas funkcija.

    Argumenti:
        request: HTTP pieprasījuma objekts
        pk: Plāna primārā atslēga (ID)

    Atgriež:
        HTTP atbildes objektu ar pāradresāciju uz plānu sarakstu pēc veiksmīgas plāna dzēšanas
    """
    try:
        plans = Plans.objects.get(id=pk)
        
        plans.delete()
        messages.success(request, "Plāns veiksmīgi izdzēsts!")
    except Plans.DoesNotExist:
        messages.error(request, "Plāns nav atrasts.")

    return redirect('plani')

@login_required
def veikalaPlans(request):
    """
    Veikala plānu lapa ar kopējo progresu un grafikiem noteiktam datumu diapazonam.

    Argumenti:
        request: HTTP pieprasījuma objekts

    Atgriež:
        HTTP atbildes objektu ar veikala plānu lapu un kontekstu
    """
    today = date.today()
    user = request.user

    # Iegūst pieejamos gadus un mēnešus izvēlnēm
    patreizejais_datums_gads = today.year
    gadi = list(range(patreizejais_datums_gads - 2, patreizejais_datums_gads + 1))
    menesu_obj = Menesis.objects.all().values_list('menesis_id', 'nosaukums')
    
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
    
    # Izveido datumu objektus no mēnešiem un gadiem
    sakuma_datums = date(sakuma_gads, sakuma_menesis, 1)
    beigu_datums = date(beigu_gads, beigu_menesis, calendar.monthrange(beigu_gads, beigu_menesis)[1])

    # Pārbauda vai beigu datums nav agrāks par sākuma datumu
    if beigu_datums < sakuma_datums:
        messages.warning(request, "Beigu datums nevar būt agrāks par sākuma datumu. Datumi tika apmainīti.")
        # Apmaina datumus
        sakuma_datums, beigu_datums = beigu_datums, sakuma_datums
        sakuma_menesis, beigu_menesis = beigu_menesis, sakuma_menesis
        sakuma_gads, beigu_gads = beigu_gads, sakuma_gads

    perioda_tesks = izveido_perioda_tekstu(sakuma_menesis, beigu_menesis, sakuma_gads, beigu_gads)

    paredzetais_progress = apreikina_paredzeto_progresu(sakuma_datums, beigu_datums)

    try:
        user_veikals = UserVeikals.objects.get(user=user)
        veikals = user_veikals.veikals
        
        menesi_intervala = aprekina_menesus_intervala(sakuma_datums, beigu_datums)
                
        veikala_plans, veikala_izpilde, veikala_proporcijas = aprekina_veikala_datus(veikals, menesi_intervala)

        kategorijas = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]

        tabulas_dati, planotais, realais, progress = veikala_grafika_dati(veikala_plans, veikala_izpilde, kategorijas)

        grafiks = veido_grafiku(paredzetais_progress, realais, planotais, progress, kategorijas, f"{veikals.nosaukums} — mēneša progress ({perioda_tesks})")
                
        context = {
            'veikals': veikals,
            'tabulas_dati': tabulas_dati,
            'chart': grafiks,
            'paredzetais_progress': round(paredzetais_progress, 1),
            'perioda_tesks': perioda_tesks,
            'sakuma_menesis': sakuma_menesis,
            'sakuma_gads': sakuma_gads,
            'beigu_menesis': beigu_menesis,
            'beigu_gads': beigu_gads,
            'menesi': menesu_obj,
            'gadi': gadi,
            'veikala_proporcijas' : veikala_proporcijas,
            'veikala_izpilde': veikala_izpilde,
        }
        
    except UserVeikals.DoesNotExist:
        messages.warning(request, "Jūsu lietotājam nav piešķirts veikals.")
        
        context = {
            'veikals': None,
            'tabulas_dati': [],
            'chart': None,
            'paredzetais_progress': 0,
            'sakuma_menesis': today.month,
            'sakuma_gads': today.year,
            'beigu_menesis': today.month,
            'beigu_gads': today.year,
            'menesi': menesu_obj,
            'gadi': gadi,
            'veikala_proporcijas' : veikala_proporcijas,
            'veikala_izpilde': veikala_izpilde,
        }
    
    return render(request, 'baze/veikala_plans.html', context)