from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from .models import Plans, Menesis

@receiver(post_migrate)
def izveidot_vaditaju(sender, **kwargs):
    if sender.name != 'baze':
        return

    vaditajs_group, created_vaditajs = Group.objects.get_or_create(name='Vadītājs')

    plans_ct = ContentType.objects.get_for_model(Plans)
    plans_permissions = Permission.objects.filter(content_type=plans_ct)

    vaditajs_group.permissions.set(plans_permissions)

@receiver(post_migrate)
def izveidot_menesus(sender, **kwargs):
    if sender.name != 'baze':
        return
    MENESI = [
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
    for num, nosaukums in MENESI:
        Menesis.objects.get_or_create(menesis_id=num, defaults={'nosaukums': nosaukums})
