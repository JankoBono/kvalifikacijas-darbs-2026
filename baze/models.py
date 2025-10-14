from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from datetime import date

# Create your models here.

class Veikals(models.Model):
    nosaukums = models.CharField(max_length=200, unique=True)
    
    def __str__(self):
        return self.nosaukums   

class UserVeikals(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    veikals = models.ForeignKey(Veikals, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username
    
def current_year():
    return date.today().year

MONTH_CHOICES = [
    ('1', 'Janvāris'),
    ('2', 'Februāris'),
    ('3', 'Marts'),
    ('4', 'Aprīlis'),
    ('5', 'Maijs'),
    ('6', 'Jūnijs'),
    ('7', 'Jūlijs'),
    ('8', 'Augusts'),
    ('9', 'Septembris'),
    ('10', 'Oktobris'),
    ('11', 'Novembris'),
    ('12', 'Decembris'),
]

class Plans(models.Model):
    lietotajs = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pieslegumi = models.IntegerField()
    iekartas = models.IntegerField()
    viedpaligi = models.IntegerField()
    aksesuari = models.IntegerField()
    atv_proprocija = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    apdr_proporcija = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    viedtelevizija = models.IntegerField()
    menesis = models.CharField(max_length=2, choices=MONTH_CHOICES, default=str(date.today().month))
    gads = models.IntegerField(default=current_year)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['lietotajs', 'menesis', 'gads'],
                name='viens_menesis_gads'
            )
        ]

    def __str__(self):
        return f"{self.lietotajs} — {self.menesis}/{self.gads}"

class Darijums(models.Model):
    lietotajs = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pieslegums = models.IntegerField(null=True, blank=True)
    atv_iekarta = models.IntegerField(null=True, blank=True)
    nom_iekarta = models.IntegerField(null=True, blank=True)
    pil_iekarta = models.IntegerField(null=True, blank=True)
    viedpaligs = models.IntegerField(null=True, blank=True)
    apdr_iekartas = models.IntegerField(null=True, blank=True)
    aksesuars = models.IntegerField(null=True, blank=True)
    viedtelevizija = models.IntegerField(null=True, blank=True)
    datums = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-datums']

    def __str__(self):
        return str(self.datums)

