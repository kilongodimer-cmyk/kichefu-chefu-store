import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from .models import CarSellRequest, Proposal


User = get_user_model()


PHONE_REGEX = re.compile(r"^\+?\d{6,15}$")


class PhoneSignupForm(UserCreationForm):
    """Formulaire d'inscription utilisant le numéro comme identifiant principal."""

    full_name = forms.CharField(
        label="Nom complet",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Nom et prenom"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        phone_field = self.fields["username"]
        phone_field.label = "Numero de telephone"
        phone_field.help_text = "Utilisez un numero unique (ex: +24381...)."
        phone_field.widget.attrs.update({"placeholder": "+243 ...", "inputmode": "tel", "autocomplete": "tel"})
        self.fields["full_name"].widget.attrs.setdefault("autocomplete", "name")
        self.fields["password1"].label = "Mot de passe"
        self.fields["password1"].widget.attrs.setdefault("autocomplete", "new-password")
        self.fields["password2"].label = "Confirmer le mot de passe"

    def clean_username(self):
        """Valide et normalise le numéro (pas d'espaces, 6-15 chiffres)."""

        username = super().clean_username()
        sanitized = username.replace(" ", "").replace("-", "")
        if not PHONE_REGEX.match(sanitized):
            raise ValidationError("Format invalide. Utilisez uniquement chiffres et un '+' optionnel.")
        return sanitized

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"].strip()
        user.last_name = ""
        user.email = user.email or ""
        if commit:
            user.save()
        return user

    def clean_full_name(self):
        value = _sanitize_text(self.cleaned_data.get("full_name"))
        if not value:
            raise ValidationError("Le nom complet est obligatoire pour l'affichage.")
        return value


class PhoneAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion dédié au couple (numero, mot de passe)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username_field = self.fields[self.username_field]
        username_field.label = "Numero de telephone"
        username_field.widget.attrs.setdefault("placeholder", "+243 ...")
        username_field.widget.attrs.setdefault("inputmode", "tel")
        username_field.widget.attrs.setdefault("autocomplete", "tel")
        self.fields["password"].label = "Mot de passe"
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")


def _sanitize_text(value):
	"""Nettoie les champs texte pour éviter le HTML et réduire les espaces."""
	if value is None:
		return value
	if not isinstance(value, str):
		return value
	cleaned = strip_tags(value)
	cleaned = " ".join(cleaned.split())
	return cleaned


class MultipleFileInput(forms.ClearableFileInput):
    """Widget HTML permettant la sélection de plusieurs fichiers à la fois."""

    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Champ custom qui impose un nombre min/max d'images."""

    def __init__(self, *args, min_files=0, max_files=None, **kwargs):
        self.min_files = min_files
        self.max_files = max_files
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = []
        if data is None:
            files = []
        elif isinstance(data, (list, tuple)):
            files = [file for file in data if file]
        else:
            files = [data]

        if self.required and not files:
            raise ValidationError("Ajoutez au moins 2 photos.")

        if self.min_files and len(files) < self.min_files:
            raise ValidationError(f"Ajoutez au moins {self.min_files} photos.")

        if self.max_files and len(files) > self.max_files:
            raise ValidationError(f"Vous pouvez ajouter au maximum {self.max_files} photos.")

        cleaned_files = []
        errors = []
        for file in files:
            try:
                cleaned_files.append(super().clean(file, initial))
            except ValidationError as exc:
                errors.extend(exc.error_list)

        if errors:
            raise ValidationError(errors)

        return cleaned_files


class CarSellRequestForm(forms.ModelForm):
    """
    Formulaire ultra-court affiché sur la page d'accueil (lead voiture).
    """

    photos = MultipleImageField(
        required=True,
        min_files=2,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
    )

    class Meta:
        """
        Métadonnées du formulaire.
        """
        model = CarSellRequest
        fields = ("name", "phone_number", "model", "year", "desired_price")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Votre nom"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "+243 ..."}),
            "model": forms.TextInput(attrs={"placeholder": "Ex: Toyota Prado"}),
            "year": forms.NumberInput(attrs={"placeholder": "Ex: 2020"}),
            "desired_price": forms.NumberInput(attrs={"placeholder": "Ex: 25000"}),
        }

    def clean_name(self):
        """
        Suppression des balises et espaces multiples pour le nom.
        
        :return: Le nom nettoyé
        """
        return _sanitize_text(self.cleaned_data.get("name"))

    def clean_phone_number(self):
        """
        Normalisation légère du numéro pour éviter les caractères parasites.
        
        :return: Le numéro de téléphone nettoyé
        """
        return _sanitize_text(self.cleaned_data.get("phone_number"))

    def clean_model(self):
        """
        Le modèle est aussi dépoussiéré avant insertion DB.
        
        :return: Le modèle nettoyé
        """
        return _sanitize_text(self.cleaned_data.get("model"))


class ProposalSellForm(forms.ModelForm):
    """
    Formulaire principal 'Vendre avec nous' multi-catégories.
    """
    photos = MultipleImageField(
        required=True,
        min_files=2,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
    )

    class Meta:
        """
        Métadonnées du formulaire.
        """
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
        """
        Nettoie les champs texte et applique les règles métier selon le type d'actif.
        
        :return: Les données nettoyées
        """
        cleaned_data = super().clean()

        for field_name in (
            "name",
            "phone_number",
            "city",
            "location_details",
            "surface_area",
            "brand",
            "model_name",
            "storage",
            "description",
        ):
            if field_name in cleaned_data:
                cleaned_data[field_name] = _sanitize_text(cleaned_data.get(field_name))

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
    """
    Formulaire admin pour importer massivement des véhicules via CSV/ZIP.
    """

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
