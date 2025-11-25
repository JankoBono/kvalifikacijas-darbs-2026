from datetime import date
from django.db.models import Sum, Avg
from .models import Darijums, Plans, Menesis
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import plotly.graph_objs as go
from plotly.offline import plot

def aprekini_veikala_dienas_datus(veikals):
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

    darijumi = Darijums.objects.filter(
        lietotajs__userveikals__veikals=veikals,
        datums__date=today
    )

    dienas_darijumi = aprekina_darijumu_summas(darijumi)

    men_veikala_darijumi = Darijums.objects.filter(
            lietotajs__userveikals__veikals=veikals,
            datums__date__gte=menesa_sakums,
            datums__date__lte=vakardienas_datums,
        )

    veikala_men_summa = aprekina_darijumu_summas(men_veikala_darijumi)

     #Izfiltrē visus veikala plānus priekš mēneša dienas mērķa aprēķina
    menesis_tagad = Menesis.objects.get(menesis_id=today.month)

    visi_plani = Plans.objects.filter(
        lietotajs__userveikals__veikals=veikals,
        menesis=menesis_tagad,
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
            kopa_atv_prop = Avg('atv_proporcija'),
        )

        # Aprēķina dienas mērķi katrai kategorijai
        dienas_merkis = {
            'pieslegumi': math.ceil(((plan_sum['kopa_pieslegumi'] or 0) - (veikala_men_summa.get('kopa_pieslegumi') or 0)) / palikusas_dienas(today)),
            'iekartas': math.ceil(((plan_sum['kopa_iekartas'] or 0) - (veikala_men_summa.get('kopa_iekartas') or 0)) / palikusas_dienas(today)),
            'viedpaligi': math.ceil(((plan_sum['kopa_viedpaligi'] or 0) - (veikala_men_summa.get('kopa_viedpaligs') or 0)) / palikusas_dienas(today)),
            'aksesuari': math.ceil(((plan_sum['kopa_aksesuari'] or 0) - (veikala_men_summa.get('kopa_aksesuars') or 0)) / palikusas_dienas(today)),
            'atvertais' : round(plan_sum['kopa_atv_prop'] or 0, 1) * 100,
            'apdrosinasana' : round(plan_sum['kopa_apdr_prop'] or 0, 1) * 100,
            'viedtelevizija': math.ceil(((plan_sum['kopa_viedtelevizija'] or 0) - (veikala_men_summa.get('kopa_viedtelevizija') or 0)) / palikusas_dienas(today)),
        }
    else:
        dienas_merkis = {}
    
    return {
        'veikals': veikals,
        'datums': today,
        'visi_summa': dienas_darijumi,
        'dienas_merkis': dienas_merkis,
    }

# Funkcija aprēķina atlikušo dienu skaitu mēnesī
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
        kopa_pieslegumi=Sum('pieslegums'),
        kopa_atv_iekarta=Sum('atv_iekarta'),
        kopa_nom_iekarta=Sum('nom_iekarta'),
        kopa_pil_iekarta=Sum('pil_iekarta'),
        kopa_viedpaligs=Sum('viedpaligs'),
        kopa_aksesuars=Sum('aksesuars'),
        kopa_viedtelevizija=Sum('viedtelevizija'),
        kopa_apdr_iekartas=Sum('apdr_iekartas'),
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
        rezultats['atv_proporcija'] = round(atv / (atv + nom), 2) * 100
    else:
        rezultats['atv_proporcija'] = 0

    # Aprēķina apdrošināto iekārtu proporciju
    if atv + nom + pil + vied != 0:
        rezultats['apdr_proporcija'] = round(apdr / (atv + nom + pil + vied), 2) * 100
    else:
        rezultats['apdr_proporcija'] = 0

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
    print(apraksts)
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
    prop_plans = Plans.objects.filter(
        lietotajs=user,
        menesis__menesis_id=today.month,
        gads=today.year
    )

    proporcijas = Darijums.objects.filter(
        lietotajs=user,
        datums__month=today.month,
        datums__year=today.year,
    ).aggregate(
        atv_iekartas=Sum('atv_iekarta'),
        apdr_iekartas=Sum('apdr_iekartas'),
        atv_iekarta=Sum('atv_iekarta'),
        nom_iekarta=Sum('nom_iekarta'),
        pil_iekarta=Sum('pil_iekarta'),
        viedpaligi=Sum('viedpaligs'),
    )

    proporcijas['iekartas'] = (proporcijas['atv_iekarta'] or 0) + (proporcijas['nom_iekarta'] or 0) + (proporcijas['pil_iekarta'] or 0)

    proporcijas['atv_proporcija'] = round((proporcijas['atv_iekartas'] or 0) / ((proporcijas['iekartas'] or 1) - (proporcijas['pil_iekarta'] or 0)) * 100, 1)
    proporcijas['apdr_proporcija'] = round((proporcijas['apdr_iekartas'] or 0) / ((proporcijas['iekartas'] or 1) + (proporcijas['viedpaligi'] or 1)) * 100, 1)
    proporcijas['atv_plans'] = round((prop_plans.aggregate(Avg('atv_proporcija'))['atv_proporcija__avg'] or 0) * 100, 0)
    proporcijas['apdr_plans'] = round((prop_plans.aggregate(Avg('apdr_proporcija'))['apdr_proporcija__avg'] or 0) * 100, 0)

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