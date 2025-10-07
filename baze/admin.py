from django.contrib import admin

from .models import Plans, Darijums, Veikals,  UserVeikals


# Unregister the default User model and register your custom one
admin.site.register(Plans)
admin.site.register(Darijums)
admin.site.register(UserVeikals)
admin.site.register(Veikals)