from django import forms

from .models import CarSellRequest


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class CarSellRequestForm(forms.ModelForm):
    photos = forms.ImageField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
    )

    class Meta:
        model = CarSellRequest
        fields = ("name", "phone_number", "model", "year", "desired_price")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Votre nom"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "+243 ..."}),
            "model": forms.TextInput(attrs={"placeholder": "Ex: Toyota Prado"}),
            "year": forms.NumberInput(attrs={"placeholder": "Ex: 2020"}),
            "desired_price": forms.NumberInput(attrs={"placeholder": "Ex: 25000"}),
        }
