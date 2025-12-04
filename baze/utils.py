from datetime import date
from django.db.models import Sum, Avg
from .models import StoreRecord, Plan, Month
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import plotly.graph_objs as go
from plotly.offline import plot

def aprekina_veikala_dienas_datus(veikals):
    """"
    Aprēķina veikala dienas datus, ieskaitot darījumu summas un dienas mērķi.

    Argumenti:
        veikals: Veikals objekts, priekš kura aprēķināt datus

    Atgriež:
        dict: Vārdnīca ar veikala datiem, darījumu summām un dienas mērķi
    """
    today = date.today()
    menesa_sakums = today + relativedelta(day=1)
    vakardienas_datums = today - timedelta(days=1)

    darijumi = StoreRecord.objects.filter(
        user__userstore__store=veikals,
        date__date=today
    )

    dienas_darijumi = aprekina_darijumu_summas(darijumi)

    men_veikala_darijumi = StoreRecord.objects.filter(
        user__userstore__store=veikals,
        date__date__gte=menesa_sakums,
        date__date__lte=vakardienas_datums,
    )

    veikala_men_summa = aprekina_darijumu_summas(men_veikala_darijumi)

    #Izfiltrē visus veikala plānus priekš mēneša dienas mērķa aprēķina
    current_month = Month.objects.get(month_id=today.month)

    visi_plani = Plan.objects.filter(
        user__userstore__store=veikals,
        month=current_month,
        year=today.year
    )

    if visi_plani.exists():
        # Apvieno visus plānus un aprēķina to summas
        plan_sum = visi_plani.aggregate(
            kopa_pieslegumi=Sum('services'),
            kopa_iekartas=Sum('devices'),
            kopa_viedpaligi=Sum('gadgets'),
            kopa_aksesuari=Sum('accessories'),
            kopa_viedtelevizija=Sum('smart_tv'),
            kopa_apdr_prop = Avg('insurance_ratio'),
            kopa_atv_prop = Avg('open_ratio'),
        )

        # Aprēķina dienas mērķi katrai kategorijai
        dienas_merkis = {
            'pieslegumi': max(0, math.ceil(((plan_sum['kopa_pieslegumi'] or 0) - (veikala_men_summa.get('kopa_pieslegumi') or 0)) / palikusas_dienas(today))),
            'iekartas': max(0, math.ceil(((plan_sum['kopa_iekartas'] or 0) - (veikala_men_summa.get('kopa_iekartas') or 0)) / palikusas_dienas(today))),
            'viedpaligi': max(0, math.ceil(((plan_sum['kopa_viedpaligi'] or 0) - (veikala_men_summa.get('kopa_viedpaligs') or 0)) / palikusas_dienas(today))),
            'aksesuari': max(0, math.ceil(((plan_sum['kopa_aksesuari'] or 0) - (veikala_men_summa.get('kopa_aksesuars') or 0)) / palikusas_dienas(today))),
            'atvertais' : round(plan_sum['kopa_atv_prop'] or 0, 1) * 100,
            'apdrosinasana' : round(plan_sum['kopa_apdr_prop'] or 0, 1) * 100,
            'viedtelevizija': max(0, math.ceil(((plan_sum['kopa_viedtelevizija'] or 0) - (veikala_men_summa.get('kopa_viedtelevizija') or 0)) / palikusas_dienas(today))),
        }
    else:
        dienas_merkis = {}

    return {
        'store': veikals,
        'date': today,
        'visi_summa': dienas_darijumi,
        'dienas_merkis': dienas_merkis,
    }

def aprekina_veikala_menesa_datus(veikals):
    """
    Aprēķina veikala mēneša kopsavilkumu, ieskaitot kopējo izpildi un salīdzinājumu ar plānu.

    Argumenti:
        veikals: Veikals objekts, priekš kura aprēķināt mēneša datus

    Atgriež:
        dict: Vārdnīca ar veikala mēneša datiem, izpildi un plānu salīdzinājumu
    """
    today = date.today()
    menesa_sakums = today + relativedelta(day=1)

    # Iegūst visus mēneša darījumus
    menesa_darijumi = StoreRecord.objects.filter(
        user__userstore__store=veikals,
        date__date__gte=menesa_sakums,
        date__date__lte=today,
    )

    menesa_summa = aprekina_darijumu_summas(menesa_darijumi)

    # Iegūst mēneša plānus
    current_month = Month.objects.get(month_id=today.month)
    visi_plani = Plan.objects.filter(
        user__userstore__store=veikals,
        month=current_month,
        year=today.year
    )

    if visi_plani.exists():
        # Apvieno visus plānus
        plan_sum = visi_plani.aggregate(
            kopa_pieslegumi=Sum('services'),
            kopa_iekartas=Sum('devices'),
            kopa_viedpaligi=Sum('gadgets'),
            kopa_aksesuari=Sum('accessories'),
            kopa_viedtelevizija=Sum('smart_tv'),
            kopa_apdr_prop=Avg('insurance_ratio'),
            kopa_atv_prop=Avg('open_ratio'),
        )

        # Aprēķina izpildes procentus
        menesa_plani = {
            'services': plan_sum['kopa_pieslegumi'] or 0,
            'devices': plan_sum['kopa_iekartas'] or 0,
            'gadgets': plan_sum['kopa_viedpaligi'] or 0,
            'accessories': plan_sum['kopa_aksesuari'] or 0,
            'smart_tv': plan_sum['kopa_viedtelevizija'] or 0,
            'atvertais': round((plan_sum['kopa_atv_prop'] or 0) * 100, 1),
            'apdrosinasana': round((plan_sum['kopa_apdr_prop'] or 0) * 100, 1),
        }

        # Aprēķina progress
        izpildes_procenti = {
            'services': round((menesa_summa.get('kopa_pieslegumi', 0) / menesa_plani['services'] * 100) if menesa_plani['services'] > 0 else 0, 1),
            'devices': round((menesa_summa.get('kopa_iekartas', 0) / menesa_plani['devices'] * 100) if menesa_plani['devices'] > 0 else 0, 1),
            'gadgets': round((menesa_summa.get('kopa_viedpaligs', 0) / menesa_plani['gadgets'] * 100) if menesa_plani['gadgets'] > 0 else 0, 1),
            'accessories': round((menesa_summa.get('kopa_aksesuars', 0) / menesa_plani['accessories'] * 100) if menesa_plani['accessories'] > 0 else 0, 1),
            'smart_tv': round((menesa_summa.get('kopa_viedtelevizija', 0) / menesa_plani['smart_tv'] * 100) if menesa_plani['smart_tv'] > 0 else 0, 1),
        }
    else:
        menesa_plani = {}
        izpildes_procenti = {}

    return {
        'store': veikals,
        'date': today,
        'month_name': current_month.name if visi_plani.exists() else '',
        'menesa_summa': menesa_summa,
        'menesa_plani': menesa_plani,
        'izpildes_procenti': izpildes_procenti,
    }

def palikusas_dienas(datums_tagad):
    """
    Aprēķina atlikušo dienu skaitu mēnesī no dotā datuma līdz mēneša beigām.

    Argumenti:
        datums_tagad (date): Datums, no kura aprēķināt atlikušo dienu skaitu

    Atgriež:
        int: Atlikušo dienu skaits mēnesī
    """
    nak_menesis = datums_tagad + relativedelta(months=+1, day=1)
    delta = nak_menesis - datums_tagad
    return delta.days

def aprekina_darijumu_summas(darijumi):
    """
    Saņem izfiltrētu darījumu queryset un atgriež vārdnīcu ar agregētiem datiem un aprēķiniem.

    Argumenti:
        darijumi: Darijums QuerySet objekts ar jau pielietotiem filtriem

    Atgriež:
        dict: Vārdnīca ar agregētiem datiem, iekārtu kopskaitu un proporcijām
    """
    if not darijumi.exists():
        return {}

    rezultats = darijumi.aggregate(
        kopa_pieslegumi=Sum('service'),
        kopa_atv_iekarta=Sum('open_device'),
        kopa_nom_iekarta=Sum('installment_device'),
        kopa_pil_iekarta=Sum('full_price_device'),
        kopa_viedpaligs=Sum('gadget'),
        kopa_aksesuars=Sum('accessory'),
        kopa_viedtelevizija=Sum('smart_tv'),
        kopa_apdr_iekartas=Sum('insured_devices'),
    )

    atv = rezultats.get('kopa_atv_iekarta') or 0
    nom = rezultats.get('kopa_nom_iekarta') or 0
    pil = rezultats.get('kopa_pil_iekarta') or 0
    vied = rezultats.get('kopa_viedpaligs') or 0
    apdr = rezultats.get('kopa_apdr_iekartas') or 0

    # Aprēķina kopējo iekārtu skaitu
    rezultats['kopa_iekartas'] = atv + nom + pil

    # Aprēķina atvērto iekārtu proporciju
    if atv + nom != 0:
        rezultats['open_ratio'] = round(atv / (atv + nom), 2) * 100
    else:
        rezultats['open_ratio'] = 0

    # Aprēķina apdrošināto iekārtu proporciju
    if atv + nom + pil + vied != 0:
        rezultats['insurance_ratio'] = round(apdr / (atv + nom + pil + vied), 2) * 100
    else:
        rezultats['insurance_ratio'] = 0

    return rezultats

def apreikina_paredzeto_progresu(sakuma_datums, beigu_datums):
    """
    Aprēķina paredzēto progresu procentos starp diviem datumiem.

    Argumenti:
        sakuma_datums (date): Perioda sākuma datums
        beigu_datums (date): Perioda beigu datums

    Atgriež:
        float: Paredzētais progress procentos
    """
    kop_dienas = (beigu_datums - sakuma_datums).days + 1
    patreiz_dienas = (date.today() - sakuma_datums).days + 1

    if kop_dienas <= 0:
        return 0.0

    paredzetais_progress = (patreiz_dienas / kop_dienas) * 100

    return min(paredzetais_progress, 100.0)

def aprekina_menesus_intervala(sakuma_datums, beigu_datums):
    """
    Aprēķina mēnešus starp diviem datumiem un atgriež tos kā sarakstu ar Menesis objektiem.

    Argumenti:
        sakuma_datums (date): Perioda sākuma datums
        beigu_datums (date): Perioda beigu datums

    Atgriež:
        list: Saraksts ar Menesis objektiem starp dotajiem datumiem
    """
    menesi = []

    while sakuma_datums <= beigu_datums:
        menesi.append((sakuma_datums.month, sakuma_datums.year))
        # Move to next month
        if sakuma_datums.month == 12:
            sakuma_datums = date(sakuma_datums.year + 1, 1, 1)
        else:
            sakuma_datums = date(sakuma_datums.year, sakuma_datums.month + 1, 1)

    return menesi

def veido_grafiku(paredzetais_progress, realais, planotais, progress, kategorijas, title):
    """
    Veido datus grafika attēlošanai, ieskaitot paredzēto progresu, reālo izpildi un plānoto izpildi.

    Argumenti:
        paredzetais_progress (float): Paredzētais progress procentos
        realais (float): Reālais izpildes procents
        planotais (float): Plānotais izpildes procents
        progress (float): Faktiskais progress procentos
        kategorijas (list): Kategoriju nosaukumi
        title (str): Grafika nosaukums

    Atgriež:
        str: HTML kods grafika attēlošanai
    """
    krasas = ["green" if val >= paredzetais_progress else "red" for val in progress]

    apraksts = [
        f"{a} / {b} ({v:.1f}%)" if b else f"{a} / 0 (0%)"
        for a, b, v in zip(realais, planotais, progress)
    ]
    trace = go.Bar(
        x=kategorijas,
        y=progress,
        marker_color=krasas,
        text=apraksts,
        textposition="auto",
    )

    layout = go.Layout(
                title=title,
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
    grafiks = plot(fig, auto_open=False, output_type="div")
    return grafiks

def aprekina_ind_lig_proporcijas(user):
    """
    Aprēķina individuālā līguma proporcijas lietotājam.

    Argumenti:
        user: Lietotājs, priekš kura aprēķināt proporcijas

    Atgriež:
        dict: Vārdnīca ar individuālā līguma proporcijām
    """
    today = date.today()
    prop_plans = Plan.objects.filter(
        user=user,
        month__month_id=today.month,
        year=today.year
    )

    proporcijas = StoreRecord.objects.filter(
        user=user,
        date__month=today.month,
        date__year=today.year,
    ).aggregate(
        apdr_iekartas=Sum('insured_devices'),
        atv_iekartas=Sum('open_device'),
        nomaksas_iekartas=Sum('installment_device'),
        pilnas_summas_iekartas=Sum('full_price_device'),
        viedpaligi=Sum('gadget'),
    )

    proporcijas['iekartas'] = (proporcijas['atv_iekartas'] or 0) + (proporcijas['nomaksas_iekartas'] or 0) + (proporcijas['pilnas_summas_iekartas'] or 0)

    proporcijas['atv_proporcija'] = round((proporcijas['atv_iekartas'] or 0) / ((proporcijas['iekartas'] or 1) - (proporcijas['pilnas_summas_iekartas'] or 0)) * 100, 1)
    proporcijas['apdr_proporcija'] = round((proporcijas['apdr_iekartas'] or 0) / ((proporcijas['iekartas'] or 1) + (proporcijas['viedpaligi'] or 1)) * 100, 1)
    proporcijas['atv_plans'] = round((prop_plans.aggregate(Avg('open_ratio'))['open_ratio__avg'] or 0) * 100, 0)
    proporcijas['apdr_plans'] = round((prop_plans.aggregate(Avg('insurance_ratio'))['insurance_ratio__avg'] or 0) * 100, 0)

    return proporcijas

def progresa_aprekins(realais, planotais):
    """
    Aprēķina progresu procentos, pamatojoties uz reālo un plānoto izpildi.

    Argumenti:
        realais (float): Reālā izpilde
        planotais (float): Plānotā izpilde

    Atgriež:
        list: Saraksts ar progresu procentos katrai kategorijai
    """
    progress = []
    for a, b in zip(realais, planotais):
        if b == 0:
            progress.append(0)
        else:
            progress.append(round(a / b * 100, 1))
    return progress

def aprekina_ind_darijumus(lietotaja_veikals):
    """
    Aprēķina individuālos darījumus priekš katra kolēģa individuālās tabulas.

    Argumenti:
        lietotaja_veikals: Lietotāja veikals, priekš kura aprēķināt darījumus

    Atgriež:
        QuerySet: Individuālo darījumu dati ar apkopotām summām katram lietotājam
    """

    visi_darijums = StoreRecord.objects.filter(user__userstore__store=lietotaja_veikals, date__date=date.today())

    ind_darijumi = visi_darijums.values('user__username','user__first_name', 'user__last_name').annotate(
        kopa_pieslegums=Sum('service'),
        kopa_atv_iekarta=Sum('open_device'),
        kopa_nom_iekarta=Sum('installment_device'),
        kopa_pil_iekarta=Sum('full_price_device'),
        kopa_viedpaligs=Sum('gadget'),
        kopa_apdr_iekartas=Sum('insured_devices'),
        kopa_aksesuars=Sum('accessory'),
        kopa_viedtelevizija=Sum('smart_tv')
    )

    return ind_darijumi

def individualie_dati(plani, palikusas_dienas, paredzetais_progress, user):
    """
    Aprēķina individuālos datus un grafikus katram pārdevējam.

    Argumenti:
        plani: Plans QuerySet objekts ar pārdevēju plāniem
        palikusas_dienas: Atlikušo dienu skaits mēnesī
        paredzetais_progress: Paredzētais progress procentos
        user: Lietotājs, priekš kura aprēķināt individuālos datus

    Atgriež:
        tuple: Saraksts ar individuālajiem datiem un grafikiem
    """
    today = date.today()
    ind_progresa_dati = []
    grafiki = []
    for p in plani:
        darijumi = StoreRecord.objects.filter(
            user=p.user,
            date__month=today.month,
            date__year=today.year,
        ).aggregate(
            services=Sum('service'),
            open_device=Sum('open_device'),
            installment_device=Sum('installment_device'),
            full_price_device=Sum('full_price_device'),
            gadgets=Sum('gadget'),
            accessories=Sum('accessory'),
            smart_tv=Sum('smart_tv'),
        )

        darijumi['devices'] = (darijumi['open_device'] or 0) + (darijumi['installment_device'] or 0) + (darijumi['full_price_device'] or 0)

        for key, val in darijumi.items():
            darijumi[key] = val or 0

        kategorijas = ["Pieslēgumi", "Iekārtas", "Viedpalīgi", "Aksesuāri", "Viedtelevīzija"]

        planotais = [
            p.services or 0,
            p.devices or 0,
            p.gadgets or 0,
            p.accessories or 0,
            p.smart_tv or 0,
        ]
        realais = [
            darijumi['services'],
            darijumi['devices'],
            darijumi['gadgets'],
            darijumi['accessories'],
            darijumi['smart_tv'],
        ]

        progress = progresa_aprekins(realais, planotais)

        if p.user == user:
            ind_progresa_dati = []
            for i, kategorija in enumerate(kategorijas):
                dienas_merkis = math.ceil((planotais[i] - realais[i]) / palikusas_dienas) if palikusas_dienas > 0 and planotais[i] > realais[i] else 0
                ind_progresa_dati.append({
                    'kategorija': kategorija,
                    'izpilde': realais[i],
                    'plans': planotais[i],
                    'progress': progress[i],
                    'dienas_merkis': round(dienas_merkis, 2)
                })

        title = f"{p.user.first_name} {p.user.last_name or p.user.username} — mēneša progress"

        grafiks = veido_grafiku(paredzetais_progress, realais, planotais, progress, kategorijas, title)
        grafiki.append(grafiks)

    return ind_progresa_dati, grafiki

def aprekina_veikala_datus(veikals, menesi_intervala):
    """
    Aprēķina veikala datus, ieskaitot plānus, izpildi un proporcijas.

    Argumenti:
        veikals: Veikals objekts, priekš kura aprēķināt datus
        menesi_intervala: Saraksts ar mēnešiem un gadiem, priekš kuriem aprēķināt datus

    Atgriež:
        tuple: Vārdnīcas ar veikala plāniem, izpildi un proporcijām
    """
    veikala_plans = {
        'services': 0,
        'devices': 0,
        'gadgets': 0,
        'accessories': 0,
        'smart_tv': 0,
    }

    veikala_izpilde = {
        'services': 0,
        'devices': 0,
        'gadgets': 0,
        'accessories': 0,
        'smart_tv': 0,
    }

    veikala_proporcijas = {
        'atv_iekartas': 0,
        'nom_iekartas': 0,
        'apdr_iekartas': 0,
        'atv_plans': 0,
        'apdr_plans': 0,
    }
    planu_skaits = 0
    # Iegūst plānus un darījumus katram mēnesim un apkopo tos
    for month, year in menesi_intervala:
        plani = Plan.objects.filter(
            user__userstore__store=veikals,
            month__month_id=month,
            year=year
        )

        planu_skaits += len(plani)            

        for p in plani:
            darijumi = StoreRecord.objects.filter(
                user=p.user,
                date__month=month,
                date__year=year,
            ).aggregate(
                services=Sum('service'),
                open_device=Sum('open_device'),
                installment_device=Sum('installment_device'),
                full_price_device=Sum('full_price_device'),
                insured_devices=Sum('insured_devices'),
                gadgets=Sum('gadget'),
                accessories=Sum('accessory'),
                smart_tv=Sum('smart_tv'),
            )

            darijumi['devices'] = (darijumi['open_device'] or 0) + (darijumi['installment_device'] or 0) + (darijumi['full_price_device'] or 0)
            
            veikala_plans['services'] += (p.services or 0)
            veikala_plans['devices'] += (p.devices or 0)
            veikala_plans['gadgets'] += (p.gadgets or 0)
            veikala_plans['accessories'] += (p.accessories or 0)
            veikala_plans['smart_tv'] += (p.smart_tv or 0)
            
            veikala_izpilde['services'] += (darijumi['services'] or 0)
            veikala_izpilde['devices'] += (darijumi['devices'] or 0)
            veikala_izpilde['gadgets'] += (darijumi['gadgets'] or 0)
            veikala_izpilde['accessories'] += (darijumi['accessories'] or 0)
            veikala_izpilde['smart_tv'] += (darijumi['smart_tv'] or 0)

            veikala_proporcijas['atv_iekartas'] += (darijumi['open_device'] or 0)
            veikala_proporcijas['nom_iekartas'] += (darijumi['installment_device'] or 0)
            veikala_proporcijas['apdr_iekartas'] += (darijumi['insured_devices'] or 0)
            veikala_proporcijas['atv_plans'] += (p.open_ratio or 0)
            veikala_proporcijas['apdr_plans'] += (p.insurance_ratio or 0)

    veikala_proporcijas['atv_plans'] = round((veikala_proporcijas['atv_plans'] / planu_skaits) * 100 if planu_skaits > 0 else 0, 0)
    veikala_proporcijas['apdr_plans'] = round((veikala_proporcijas['apdr_plans'] / planu_skaits) * 100 if planu_skaits > 0 else 0, 0)
    veikala_proporcijas['atv_proporcija'] = round((veikala_proporcijas['atv_iekartas'] or 0) / ((veikala_proporcijas['atv_iekartas'] or 1) + (veikala_proporcijas['nom_iekartas'] or 1)) * 100, 1)
    veikala_proporcijas['apdr_proporcija'] = round((veikala_proporcijas['apdr_iekartas'] or 0) / ((veikala_izpilde['devices'] or 1) + (veikala_izpilde['gadgets'] or 1)) * 100, 1)

    return veikala_plans, veikala_izpilde, veikala_proporcijas

def veikala_grafika_dati(veikala_plans, veikala_izpilde, kategorijas):
    """
    Aprēķina veikala grafika datus, ieskaitot plānoto un reālo izpildi katrai kategorijai.

    Argumenti:
        veikala_plans: Vārdnīca ar veikala plāniem katrai kategorijai
        veikala_izpilde: Vārdnīca ar veikala izpildi katrai kategorijai
        kategorijas: Saraksts ar kategoriju nosaukumiem

    Atgriež:
        tuple: Saraksts ar tabulas datiem, plānoto izpildi, reālo izpildi un progresu katrai kategorijai
    """
    kategoriju_atslegas = ['services', 'devices', 'gadgets', 'accessories', 'smart_tv']
    
    tabulas_dati = []
    planotais = []
    realais = []
    progress = []
    
    for i, kategorija in enumerate(kategorijas):
        key = kategoriju_atslegas[i]
        plans_val = veikala_plans[key]
        izpilde_val = veikala_izpilde[key]
        progress_val = progresa_aprekins([izpilde_val], [plans_val])[0]

        tabulas_dati.append({
            'kategorija': kategorija,
            'izpilde': izpilde_val,
            'plans': plans_val,
            'progress': progress_val
        })

        planotais.append(plans_val)
        realais.append(izpilde_val)
        progress.append(progress_val)

    return tabulas_dati, planotais, realais, progress

def izveido_perioda_tekstu(sakuma_menesis, beigu_menesis, sakuma_gads, beigu_gads):
    """
    Izveido perioda tekstu no dotajiem mēnešiem un gadiem.

    Argumenti:
        sakuma_menesis (int): Sākuma mēnesis
        beigu_menesis (int): Beigu mēnesis
        sakuma_gads (int): Sākuma gads
        beigu_gads (int): Beigu gads

    Atgriež:
        str: Perioda teksts grafika nosaukumam
    """
    try:
        sakuma_menesis_obj = Month.objects.get(month_id=sakuma_menesis)
        beigu_menesis_obj = Month.objects.get(month_id=beigu_menesis)
        
        # Izveido perioda tekstu priekš grafika nosaukuma
        if sakuma_menesis == beigu_menesis and sakuma_gads == beigu_gads:
            perioda_teksts = f"{sakuma_menesis_obj.name} {sakuma_gads}"
        else:
            perioda_teksts = f"{sakuma_menesis_obj.name} {sakuma_gads} - {beigu_menesis_obj.name} {beigu_gads}"
    except Month.DoesNotExist:
        perioda_teksts = f"{sakuma_menesis}/{sakuma_gads} - {beigu_menesis}/{beigu_gads}"

    return perioda_teksts

    