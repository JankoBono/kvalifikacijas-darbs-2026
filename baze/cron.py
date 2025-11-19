# baze/cron.py
from django_cron import CronJobBase, Schedule
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from datetime import date
from .models import Veikals, UserVeikals
from .utils import aprekini_veikala_dienas_datus

class SutitDienasAtskaiti(CronJobBase):
    RUN_AT_TIMES = ['22:00'] # Katru dienu plkst. 22:00
    
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'baze.sutit_dienas_atskaiti'  
    
    def do(self):
        today = date.today()
        
        # Iegūst visus veikalus
        veikali = Veikals.objects.all()
        
        for veikals in veikali:
            # Iegūst Vadītājs lietotājus šim veikalam
            vaditaji = User.objects.filter(
                groups__name='Vadītājs',
                userveikals__veikals=veikals
            )
                        
            if not vaditaji.exists():
                continue
            
            # Iegūst veikala dienas datus
            veikala_dati = aprekini_veikala_dienas_datus(veikals)
            
            # Sagatavo kontekstu e-pasta veidnei
            context = {
                'veikals_nosaukums': veikals.nosaukums,
                'datums': today.strftime('%d.%m.%Y'),
                'visi_summa': veikala_dati['visi_summa'],
                'dienas_merkis': veikala_dati['dienas_merkis'],
            }
            
            # Renderē e-pastu
            html_zinojums = render_to_string('baze/epasts_dienas.html', context)
            teksta_zinojums = strip_tags(html_zinojums)
            
            # Nosūta e-pastu visiem Vadītājs lietotājiem
            sanemeju_epasti = [lietotajs.email for lietotajs in vaditaji if lietotajs.email]
            
            if sanemeju_epasti:
                print(f"Nosūta dienas kopsavilkuma e-pastu veikalam {veikals.nosaukums} uz {sanemeju_epasti}")
                send_mail(
                    subject=f'Dienas kopsavilkums - {veikals.nosaukums} - {today.strftime("%d.%m.%Y")}',
                    message=teksta_zinojums,
                    from_email=None,  # Izmanto DEFAULT_FROM_EMAIL
                    recipient_list=sanemeju_epasti,
                    html_message=html_zinojums,
                    fail_silently=False,
                )
                print(f"E-pasts veiksmīgi nosūtīts veikalam {veikals.nosaukums}")
            else:
                print(f"Nav e-pasta adrešu vadītājiem veikalam {veikals.nosaukums}")