from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Plans, Darijums

class CustomUserAdmin(UserAdmin):
    # Add the custom fields to the fields shown in the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('vards', 'uzvards', 'veikals')}),
    )
    # Add the custom fields to the list display view in the admin
    list_display = UserAdmin.list_display + ('vards', 'uzvards', 'veikals')

# Unregister the default User model and register your custom one
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Plans)
admin.site.register(Darijums)