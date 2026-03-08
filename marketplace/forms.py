from django import forms

from .models import CarSellRequest, Proposal


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


class ProposalSellForm(forms.ModelForm):
    photos = forms.ImageField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
    )

    class Meta:
        model = Proposal
        fields = (
            "name",
            "phone_number",
            "asset_type",
            "city",
            "location_details",
            "surface_area",
            "brand",
            "model_name",
            "year",
            "mileage",
            "storage",
            "transmission",
            "fuel_type",
            "item_condition",
            "description",
            "desired_price",
        )
        labels = {
            "asset_type": "Type d'element",
            "city": "Ville",
            "location_details": "Localisation precise",
            "surface_area": "Surface / dimension",
            "brand": "Marque ou nom de l'article",
            "model_name": "Modele",
            "year": "Annee",
            "mileage": "Kilometrage",
            "storage": "Stockage",
            "transmission": "Transmission",
            "fuel_type": "Carburant",
            "item_condition": "Etat",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Votre nom complet"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "+243 ..."}),
            "asset_type": forms.Select(),
            "city": forms.TextInput(attrs={"placeholder": "Ex: Lubumbashi"}),
            "location_details": forms.TextInput(attrs={"placeholder": "Ex: Quartier, avenue, repere"}),
            "surface_area": forms.TextInput(attrs={"placeholder": "Ex: 20m x 30m / 95 m2"}),
            "brand": forms.TextInput(attrs={"placeholder": "Ex: Toyota / Samsung / Apple / Canon"}),
            "model_name": forms.TextInput(attrs={"placeholder": "Ex: Prado TX / iPhone 12"}),
            "year": forms.NumberInput(attrs={"placeholder": "Ex: 2020"}),
            "mileage": forms.NumberInput(attrs={"placeholder": "Ex: 85000"}),
            "storage": forms.TextInput(attrs={"placeholder": "Ex: 128GB"}),
            "transmission": forms.Select(),
            "fuel_type": forms.Select(),
            "item_condition": forms.Select(),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Donnez un maximum d'informations: etat reel, documents, pannes, options, prix negociable, urgence, etc.",
                }
            ),
            "desired_price": forms.NumberInput(attrs={"placeholder": "Ex: 15000"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        asset_type = cleaned_data.get("asset_type")

        required_common = ("city", "item_condition", "description")
        required_by_type = {
            "car": ("brand", "model_name", "year", "mileage", "transmission", "fuel_type"),
            "phone": ("brand", "model_name", "storage"),
            "accessory": ("brand",),
            "house": ("location_details", "surface_area"),
            "land": ("location_details", "surface_area"),
        }

        for field_name in required_common:
            if not cleaned_data.get(field_name):
                self.add_error(field_name, "Ce champ est obligatoire pour analyser votre proposition.")

        for field_name in required_by_type.get(asset_type, ()):
            if not cleaned_data.get(field_name):
                self.add_error(field_name, "Ce champ est obligatoire pour ce type d'element.")

        description = (cleaned_data.get("description") or "").strip()
        if description and len(description) < 25:
            self.add_error("description", "Ajoutez plus de details (minimum 25 caracteres).")

        return cleaned_data


class CarCSVImportForm(forms.Form):
    DUPLICATE_STRATEGIES = (
        ("skip", "Ignorer les doublons"),
        ("update", "Mettre a jour les doublons"),
    )

    csv_file = forms.FileField(
        label="Fichier CSV",
        help_text="Colonnes requises: marque, modele, annee, kilometrage, prix, description, image",
    )
    images_zip = forms.FileField(
        label="Archive ZIP des images (optionnel)",
        required=False,
        help_text="Le CSV peut contenir plusieurs images dans la colonne image, separees par | ; ou ,",
    )
    duplicate_strategy = forms.ChoiceField(
        label="Gestion des doublons",
        choices=DUPLICATE_STRATEGIES,
        initial="skip",
    )
