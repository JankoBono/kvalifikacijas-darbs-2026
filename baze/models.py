from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    vards = models.CharField(max_length=200)
    uzvards = models.CharField(max_length=200)
    veikals = models.CharField(max_length=200)
    pass


class Plans(models.Model):
    lietotajs = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    pieslegumi = models.IntegerField()
    iekartas = models.IntegerField()
    viedpaligi = models.IntegerField()
    aksesuari = models.IntegerField()
    atv_proprocija = models.DecimalField(max_digits=5, decimal_places=2)
    apdr_proporcija = models.DecimalField(max_digits=5, decimal_places=2)
    viedtelevizija = models.IntegerField()
    menesis = models.CharField(max_length=20)
    gads = models.IntegerField()

    def __str__(self):
        return self.menesis

class Darijums(models.Model):
    lietotajs = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    pieslegums = models.IntegerField()
    atv_iekarta = models.IntegerField()
    nom_iekarta = models.IntegerField()
    pil_iekarta = models.IntegerField()
    viedpaligs = models.IntegerField()
    apdr_iekartas = models.IntegerField()
    aksesuars = models.IntegerField()
    viedtelevizija = models.IntegerField()
    datums = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.datums)

