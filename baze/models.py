from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from datetime import date

# Create your models here.

class Store(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class UserStore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} / {self.store.name if self.store else 'Nav veikala'}"

def current_year():
    return date.today().year

def current_month():
    month_num_now = date.today().month

    try:
        return Month.objects.get(month_id=month_num_now)
    except ObjectDoesNotExist:
        return None

class Month(models.Model):
    month_id = models.PositiveSmallIntegerField(unique=True)  # 1–12
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['month_id']

    def __str__(self):
        return self.name

class Plan(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    services = models.IntegerField()
    devices = models.IntegerField()
    gadgets = models.IntegerField()
    accessories = models.IntegerField()
    open_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    insurance_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.5)
    smart_tv = models.IntegerField()
    month = models.ForeignKey(Month, on_delete=models.SET_NULL, null=True, default=current_month)
    year = models.IntegerField(default=current_year)

    def __str__(self):
        return f"{self.user} — {self.month}/{self.year}"

class StoreRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    service = models.IntegerField(null=True, blank=True)
    open_device = models.IntegerField(null=True, blank=True)
    installment_device = models.IntegerField(null=True, blank=True)
    full_price_device = models.IntegerField(null=True, blank=True)
    gadget = models.IntegerField(null=True, blank=True)
    insured_devices = models.IntegerField(null=True, blank=True)
    accessory = models.IntegerField(null=True, blank=True)
    smart_tv = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.date)
