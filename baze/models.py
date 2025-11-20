from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
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
        return f"{self.user.username} / {self.veikals.nosaukums if self.veikals else 'Nav veikala'}"
    
def current_year():
    return date.today().year

def menesis_tagad():
    menesa_nr_tagad = date.today().month

    try:
        return Menesis.objects.get(menesis_id=menesa_nr_tagad)
    except ObjectDoesNotExist:
        return None

class Menesis(models.Model):
    menesis_id = models.PositiveSmallIntegerField(unique=True)  # 1–12
    nosaukums = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['menesis_id']

    def __str__(self):
        return self.nosaukums

class Plans(models.Model):
    lietotajs = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pieslegumi = models.IntegerField()
    iekartas = models.IntegerField()
    viedpaligi = models.IntegerField()
    aksesuari = models.IntegerField()
    atv_proporcija = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    apdr_proporcija = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    viedtelevizija = models.IntegerField()
    menesis = models.ForeignKey(Menesis, on_delete=models.SET_NULL, null=True, default=menesis_tagad)
    gads = models.IntegerField(default=current_year)


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
    datums = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-datums']

    def __str__(self):
        return str(self.datums)

