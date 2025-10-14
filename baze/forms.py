from django.forms import ModelForm
from django.contrib.auth import get_user_model
from .models import Darijums, Plans, UserVeikals

User = get_user_model()
class DarijumsForm(ModelForm):
    class Meta:
        model = Darijums
        exclude = ('lietotajs', 'datums',) 

class PlansForm(ModelForm):
    class Meta:
        model = Plans
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        if user:
            try:
                veikals = UserVeikals.objects.get(user=user).veikals
                                
                self.fields['lietotajs'].queryset = User.objects.filter(
                    userveikals__veikals=veikals
                )
                
            except (AttributeError, UserVeikals.DoesNotExist):
                self.fields['lietotajs'].queryset = User.objects.none()