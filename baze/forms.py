from django.forms import ModelForm
from .models import Darijums, Plans

class DarijumsForm(ModelForm):
    class Meta:
        model = Darijums
        exclude = ('lietotajs', 'datums',) 

class PlansForm(ModelForm):
    class Meta:
        model = Plans
        fields = '__all__'