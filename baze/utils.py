from datetime import date
from django.db.models import Sum, Avg
from .models import Darijums, Plans, Menesis
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import math
import math 
import calendar


def aprekini_veikala_dienas_datus(veikals):
    
    today = date.today()
    menesa_sakums = today + relativedelta(day=1)
    vakardienas_datums = today - timedelta(days=1)

    darijumi = Darijums.objects.filter(
        lietotajs__userveikals__veikals=veikals,
        datums__date=today
    )

    # Aprēķina dienas izpildi
    dienas_darijumi = darijumi.aggregate(
        kopa_pieslegumi=Sum('pieslegums'),
        kopa_atv_iekarta=Sum('atv_iekarta'),
        kopa_nom_iekarta=Sum('nom_iekarta'),
        kopa_pil_iekarta=Sum('pil_iekarta'),
        kopa_viedpaligs=Sum('viedpaligs'),
        kopa_aksesuars=Sum('aksesuars'),
        kopa_viedtelevizija=Sum('viedtelevizija'),
        kopa_apdr_iekartas=Sum('apdr_iekartas'),
    )
    
    atv = dienas_darijumi.get('kopa_atv_iekarta') or 0
    nom = dienas_darijumi.get('kopa_nom_iekarta') or 0
    pil = dienas_darijumi.get('kopa_pil_iekarta') or 0
    vied = dienas_darijumi.get('kopa_viedpaligs') or 0
    apdr = dienas_darijumi.get('kopa_apdr_iekartas') or 0

    # Aprēķina kopējo iekārtu skaitu
    dienas_darijumi['iekartas_kopa'] = atv + nom + pil

    # Aprēķina atvērto iekārtu proporciju
    if atv + nom != 0:
        dienas_darijumi['atv_proporcija'] = round(atv / (atv + nom), 2) * 100
    else:
        dienas_darijumi['atv_proporcija'] = 0

    # Aprēķina apdrošināto iekārtu proporciju
    if atv + nom + pil + vied !=0:
        dienas_darijumi['apdr_proporcija'] = round(apdr / (atv + nom + pil + vied), 2) * 100
    else:
        dienas_darijumi['apdr_proporcija'] = 0

    men_veikala_darijumi = Darijums.objects.filter(
            lietotajs__userveikals__veikals=veikals,
            datums__date__gte=menesa_sakums,
            datums__date__lte=vakardienas_datums,
        )

    if men_veikala_darijumi.exists():
        veikala_men_summa = men_veikala_darijumi.aggregate(
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
    
    return {
        'veikals': veikals,
        'datums': today,
        'visi_summa': dienas_darijumi,
        'dienas_merkis': dienas_merkis,
    }

# Funkcija aprēķina atlikušo dienu skaitu mēnesī
def palikusas_dienas(datums_tagad):
    nak_menesis = datums_tagad + relativedelta(months=+1, day=1)
    delta = nak_menesis - datums_tagad
    return delta.days