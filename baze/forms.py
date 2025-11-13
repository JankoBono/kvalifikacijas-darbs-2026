from django.forms import ModelForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Darijums, Plans, UserVeikals

User = get_user_model()
class DarijumsForm(ModelForm):
    class Meta:
        model = Darijums
        exclude = ('lietotajs', 'datums',)

        labels = {
                'pieslegums': 'Pieslēgums',
                'atv_iekarta': 'Atvērtā iekārta',
                'nom_iekarta': 'Nomaksas iekārta',
                'pil_iekarta': 'Pilnas cenas iekārta',
                'viedpaligs': 'Viedpalīgs',
                'apdr_iekartas': 'Apdrošināta iekārta',
                'aksesuars': 'Aksesuārs',
                'viedtelevizija': 'Viedtelevīzija',
            }

    def clean(self):
        derigi_dati = super().clean()
        
        pozicijas = [
            'pieslegums', 'atv_iekarta', 'nom_iekarta', 'pil_iekarta',
            'viedpaligs', 'aksesuars', 'viedtelevizija'
        ]
        
        for nosaukums in pozicijas:
            vertiba = derigi_dati.get(nosaukums)
            if vertiba is not None and vertiba < 0:
                self.add_error(nosaukums, 'Vērtība nevar būt negatīva.')
        
        return derigi_dati
        
class PlansForm(ModelForm):
    class Meta:
        model = Plans
        fields = '__all__'
        labels = {
            'lietotajs': 'Lietotājs',
            'pieslegumi': 'Pieslēgumi',
            'iekartas': 'Iekārtas',
            'viedpaligi': 'Viedpalīgi',
            'aksesuari': 'Aksesuāri',
            'atv_proprocija': 'Atvērtā līguma proporcija',
            'apdr_proporcija': 'Apdrošināšanas proporcija',
            'viedtelevizija': 'Viedtelevīzija',
            'menesis': 'Mēnesis',
            'gads': 'Gads',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        if user:
            try:
                veikals = UserVeikals.objects.get(user=user).veikals
                                
                self.fields['lietotajs'].queryset = User.objects.filter(
                    userveikals__veikals=veikals
                )
                
            except UserVeikals.DoesNotExist:
                self.fields['lietotajs'].queryset = User.objects.none()

    def clean(self):
        derigi_dati = super().clean()
        lietotajs = derigi_dati.get('lietotajs')
        menesis = derigi_dati.get('menesis')
        gads = derigi_dati.get('gads')

        pozicijas = [
            'pieslegumi', 'iekartas', 'viedpaligi', 'aksesuari', 'viedtelevizija',
            'atv_proprocija', 'apdr_proporcija'
        ]

        for field in pozicijas:
            vertiba = derigi_dati.get(field)
            if vertiba is not None and vertiba < 0:
                self.add_error(field, 'Vērtība nevar būt negatīva.')

        for prop_field in ['atv_proprocija', 'apdr_proporcija']:
            vertiba = derigi_dati.get(prop_field)
            if vertiba is not None and not (0 <= vertiba <= 1):
                self.add_error(prop_field, 'Proporcijai jābūt starp 0 un 1.')

        if lietotajs and menesis and gads:
            eksiste = Plans.objects.filter(
                lietotajs=lietotajs,
                menesis=menesis,
                gads=gads
            ).exclude(pk=self.instance.pk).exists()

            if eksiste:
                raise ValidationError(
                    "Šim lietotājam jau ir izveidots plāns šim mēnesim un gadam."
                )

        return derigi_dati