from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite
from .models import Plan, StoreRecord, Store, UserStore, Month

# Also register with default admin site for backwards compatibility
admin.site.register(Plan)
admin.site.register(StoreRecord)
admin.site.register(UserStore)
admin.site.register(Store)
admin.site.register(Month)


# Customize the admin interface titles
admin.site.site_header = "Bāzes Administrācija"
User._meta.verbose_name = "Lietotājs"
User._meta.verbose_name_plural = "Lietotāji"
User._meta.get_field('username').verbose_name = "Lietotājvārds"
User._meta.get_field('email').verbose_name = "E-pasts"
User._meta.get_field('first_name').verbose_name = "Vārds"
User._meta.get_field('last_name').verbose_name = "Uzvārds"
User._meta.get_field('is_staff').verbose_name = "Personāla statuss"
User._meta.get_field('is_active').verbose_name = "Aktīvs"
User._meta.get_field('password').verbose_name = "Parole"

Group._meta.verbose_name = "Loma"
Group._meta.verbose_name_plural = "Lomas"
Group._meta.get_field('name').verbose_name = "Nosaukums"
Group._meta.get_field('permissions').verbose_name = "Atļaujas"

StoreRecord._meta.verbose_name = "Darījums"
StoreRecord._meta.verbose_name_plural = "Darījumi"
StoreRecord._meta.get_field('user').verbose_name = "Lietotājs"
StoreRecord._meta.get_field('date').verbose_name = "Datums"
StoreRecord._meta.get_field('service').verbose_name = "Pieslēgums"
StoreRecord._meta.get_field('open_device').verbose_name = "Atvērtā iekārta"
StoreRecord._meta.get_field('installment_device').verbose_name = "Nomaksas iekārta"
StoreRecord._meta.get_field('full_price_device').verbose_name = "Pilnas cenas iekārta"
StoreRecord._meta.get_field('gadget').verbose_name = "Viedpalīgs"
StoreRecord._meta.get_field('accessory').verbose_name = "Aksesuārs"
StoreRecord._meta.get_field('insured_devices').verbose_name = "Apdrošināta iekārta"
StoreRecord._meta.get_field('smart_tv').verbose_name = "Viedtelevīzija"

Plan._meta.verbose_name = "Plāns"
Plan._meta.verbose_name_plural = "Plāni"
Plan._meta.get_field('user').verbose_name = "Lietotājs"
Plan._meta.get_field('services').verbose_name = "Pieslēgumi"
Plan._meta.get_field('devices').verbose_name = "Iekārtas"
Plan._meta.get_field('gadgets').verbose_name = "Viedpalīgi"
Plan._meta.get_field('accessories').verbose_name = "Aksesuāri"
Plan._meta.get_field('open_ratio').verbose_name = "Atvērto iekārtu proporcija"
Plan._meta.get_field('insurance_ratio').verbose_name = "Apdrošināto iekārtu proporcija"
Plan._meta.get_field('smart_tv').verbose_name = "Viedtelevīzija"
Plan._meta.get_field('month').verbose_name = "Mēnesis"
Plan._meta.get_field('year').verbose_name = "Gads"

Store._meta.verbose_name = "Veikals"
Store._meta.verbose_name_plural = "Veikali"
Store._meta.get_field('name').verbose_name = "Nosaukums"

UserStore._meta.verbose_name = "Lietotāja Veikals"
UserStore._meta.verbose_name_plural = "Lietotāju Veikali"
UserStore._meta.get_field('user').verbose_name = "Lietotājs"
UserStore._meta.get_field('store').verbose_name = "Veikals"

Month._meta.verbose_name = "Mēnesis"
Month._meta.verbose_name_plural = "Mēneši"