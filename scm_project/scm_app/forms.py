from django import forms
from .models import Plan, SalesOffer, ProductionCapacity, PurchaseOffer, Demand
from django.forms.models import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.core.exceptions import ValidationError
import datetime


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label='',
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Nazwa użytkownika'})
    )
    password = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': 'Hasło'}),
    )

class PlanAdminForm(forms.ModelForm):
    class Meta:
        model = Plan
        exclude = ()

    def clean(self):
        status = self.instance.calculate_plan_status()
        if (status == 'zakończono składanie ofert' or status == 'nieaktywny'):
            raise forms.ValidationError("nie można wprowadzać zmian w nieaktywnych aukcjach")
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        schedule_beginning = self.cleaned_data.get('schedule_beginning')

        if start_date < datetime.date.today()+datetime.timedelta(days=1):
            raise forms.ValidationError("Rozpoczecie aukcji nalezy oglaszac co najmniej 24h przed rozpoczęciem zbierania ofert")
        if start_date >= end_date:
            raise forms.ValidationError("Aukcja musi trwac co najmniej 24h, wprowadz poprawną datę zakończenia")
        if schedule_beginning <= end_date:
            raise forms.ValidationError("Planowany harmonogram musi dotyczyć okresu po zakończeniu zbierania ofert")
        return self.cleaned_data

class SalesOfferForm(forms.ModelForm):
    class Meta:
        model = SalesOffer
        fields = ('setup_cost', 'stock_level', 'stock_cost', 'max_stock_capacity')
        exclude = ('number',)
    def __init__(self, *args, **kwargs):
        super(SalesOfferForm, self).__init__(*args, **kwargs)
        self.fields['setup_cost'].label = 'Koszt początkowy'
        self.fields['stock_level'].label = 'Stan magazynu'
        self.fields['stock_cost'].label = 'Jednostkowy koszt magazynowania'
        self.fields['max_stock_capacity'].label = 'Maksymalna pojemność magazynu'

class ProductionCapacityForm(forms.ModelForm):
    class Meta:
        model = ProductionCapacity
        exclude = ('number',)
    def __init__(self, *args, **kwargs):
        super(ProductionCapacityForm, self).__init__(*args, **kwargs)
        self.fields['production_level'].label = 'Górny próg produkcji'
        self.fields['production_cost'].label = 'Jednostkowy koszt produkcji'
        
ProductionCapacityFormSet = inlineformset_factory(SalesOffer, ProductionCapacity, form=ProductionCapacityForm, extra=1)


class PurchaseOfferForm(forms.ModelForm):
    class Meta:
        model = PurchaseOffer
        fields = ('retail_unit_price', 'stock_level', 'stock_cost', 'max_stock_capacity')
    def __init__(self, *args, **kwargs):
        super(PurchaseOfferForm, self).__init__(*args, **kwargs)
        self.fields['retail_unit_price'].label = 'Proponowana cena kupna'
        self.fields['stock_level'].label = 'Stan magazynu'
        self.fields['stock_cost'].label = 'Jednostkowy koszt magazynowania'
        self.fields['max_stock_capacity'].label = 'Maksymalna pojemność magazynu'

class DemandForm(forms.ModelForm):
    class Meta:
        model = Demand
        exclude = ('number',)
    def __init__(self, *args, **kwargs):
        super(DemandForm, self).__init__(*args, **kwargs)
        self.fields['demand'].label = ''
        self.fields['demand'].required=True

def setDemandFormSet(num_of_demand):
    DemandFormSet = inlineformset_factory(PurchaseOffer, Demand, form=DemandForm, extra=num_of_demand, max_num=num_of_demand, can_delete=False)
    return DemandFormSet