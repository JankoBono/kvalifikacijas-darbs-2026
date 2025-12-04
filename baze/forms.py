from django import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import StoreRecord, Plan, UserStore

User = get_user_model()
class StoreRecordForm(ModelForm):
    class Meta:
        model = StoreRecord
        exclude = ('user', 'date',)

        labels = {
                'service': 'Pieslēgums',
                'open_device': 'Atvērtā iekārta',
                'installment_device': 'Nomaksas iekārta',
                'full_price_device': 'Pilnas cenas iekārta',
                'gadget': 'Viedpalīgs',
                'insured_devices': 'Apdrošināta iekārta',
                'accessory': 'Aksesuārs',
                'smart_tv': 'Viedtelevīzija',
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        """
        Pārbauda, vai neviena no laukiem nav negatīva un
        vai vismaz vienam laukam ir vērtība lielāka par 0.

        Returns:
            dict: Derīgie dati pēc validācijas.
            vai
            kļūda tiek pievienota, ja validācija neizdodas.
        """
        derigi_dati = super().clean()

        pozicijas = [
            'service', 'open_device', 'installment_device', 'full_price_device',
            'gadget', 'accessory', 'smart_tv'
        ]

        for nosaukums in pozicijas:
            vertiba = derigi_dati.get(nosaukums)
            if vertiba is not None and vertiba < 0:
                self.add_error(nosaukums, 'Vērtība nevar būt negatīva.')

        # Check that at least one field has a value > 0
        ir_vertiba = False
        for nosaukums in pozicijas:
            vertiba = derigi_dati.get(nosaukums)
            if vertiba is not None and vertiba > 0:
                ir_vertiba = True
                break

        if not ir_vertiba:
            self.add_error(nosaukums, 'Vismaz vienam laukam jābūt aizpildītam ar vērtību lielāku par 0.')

        return derigi_dati
        
class PlanForm(ModelForm):
    class Meta:
        model = Plan
        fields = '__all__'
        labels = {
            'user': 'Lietotājs',
            'services': 'Pieslēgumi',
            'devices': 'Iekārtas',
            'gadgets': 'Viedpalīgi',
            'accessories': 'Aksesuāri',
            'open_ratio': 'Atvērtā līguma proporcija',
            'insurance_ratio': 'Apdrošināšanas proporcija',
            'smart_tv': 'Viedtelevīzija',
            'month': 'Mēnesis',
            'year': 'Gads',
        }
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control',
                'oninvalid': "this.setCustomValidity('Lūdzu, izvēlieties lietotāju!')",
                'oninput': "this.setCustomValidity('')"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            try:
                store= UserStore.objects.get(user=user).store

                self.fields['user'].queryset = User.objects.filter(
                    userstore__store=store
                )

            except UserStore.DoesNotExist:
                self.fields['user'].queryset = User.objects.none()

        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        """
        Pārbauda, vai neviena no laukiem nav negatīva,
        un vai nav izveidots plāns konkrētajam lietotājam, mēnesim un gadam.

        Atgriež:
            dict: Derīgie dati pēc validācijas.
            vai
            kļūda tiek pievienota, ja validācija neizdodas.
        """
        derigi_dati = super().clean()
        user= derigi_dati.get('user')
        month= derigi_dati.get('month')
        year= derigi_dati.get('year')

        pozicijas = [
            'services', 'devices', 'gadgets', 'accessories', 'smart_tv',
            'open_ratio', 'insurance_ratio'
        ]

        for field in pozicijas:
            vertiba = derigi_dati.get(field)
            if vertiba is not None and vertiba < 0:
                self.add_error(field, 'Vērtība nevar būt negatīva.')

        for prop_field in ['open_ratio', 'insurance_ratio']:
            vertiba = derigi_dati.get(prop_field)
            if vertiba is not None and not (0 <= vertiba <= 1):
                self.add_error(prop_field, 'Proporcijai jābūt starp 0 un 1.')

        if user and month and year:
            eksiste = Plan.objects.filter(
                user=user,
                month=month,
                year=year
            ).exclude(pk=self.instance.pk).exists()

            if eksiste:
                raise ValidationError(
                    "Šim lietotājam jau ir izveidots plāns šim mēnesim un gadam."
                )

        return derigi_dati