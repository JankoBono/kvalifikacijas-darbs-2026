from django.forms import ModelForm
from .models import Darijums

class DarijumsForm(ModelForm):
    class Meta:
        model = Darijums
        fields = '__all__'