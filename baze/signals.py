from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from .models import Plan, Month

@receiver(post_migrate)
def izveidot_vaditaju(sender, **kwargs):
    """
    Izveido 'Vadītājs' un 'Pārdevējs' grupas pēc migrācijas.
    'Vadītājs' grupa saņem visas 'Plan' modeļa atļaujas.
    'Pārdevējs' grupa tiek izveidota kā pamata lietotāja loma.
    """
    if sender.name != 'baze':
        return

    # Create Vadītājs group with Plan permissions
    vaditajs_group, created_vaditajs = Group.objects.get_or_create(name='Vadītājs')

    plans_ct = ContentType.objects.get_for_model(Plan)
    plans_permissions = Permission.objects.filter(content_type=plans_ct)

    vaditajs_group.permissions.set(plans_permissions)

    # Create Pārdevējs group (basic user role)
    pardevejas_group, created_pardevejas = Group.objects.get_or_create(name='Pārdevējs')



@receiver(post_save, sender=User)
def pievienot_noklusejuma_grupu(sender, instance, created, **kwargs):
    """
    Piesaista jauniem lietotājiem 'Pārdevējs' grupu pēc izveides.
    """

    if created:
        pardevejas_group, _ = Group.objects.get_or_create(name='Pārdevējs')
        instance.groups.add(pardevejas_group)

@receiver(post_migrate)
def izveidot_menesus(sender, **kwargs):
    """
    Izveido mēnešu ierakstus datu bāzē pēc migrācijas.
    """
    if sender.name != 'baze':
        return
    MONTHS = [
        (1, 'Janvāris'),
        (2, 'Februāris'),
        (3, 'Marts'),
        (4, 'Aprīlis'),
        (5, 'Maijs'),
        (6, 'Jūnijs'),
        (7, 'Jūlijs'),
        (8, 'Augusts'),
        (9, 'Septembris'),
        (10, 'Oktobris'),
        (11, 'Novembris'),
        (12, 'Decembris'),
    ]
    for num, nosaukums in MONTHS:
        Month.objects.get_or_create(month_id=num, defaults={'name': nosaukums})
