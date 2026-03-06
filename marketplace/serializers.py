from urllib.parse import quote

from rest_framework import serializers

from .models import (
    Accessory,
    Car,
    CarImage,
    Phone,
    PhoneImage,
    Proposal,
    ProposalImage,
    RealEstate,
    RealEstateImage,
)


WHATSAPP_MESSAGE = "Bonjour, je suis intéressé par ce produit sur KICHEFU-CHEFU STORE."


def build_whatsapp_link():
    return f"https://wa.me/243000000000?text={quote(WHATSAPP_MESSAGE)}"


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ("id", "car", "image", "created_at")
        read_only_fields = ("id", "created_at")


class CarSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    whatsapp_link = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = (
            "id",
            "slug",
            "brand",
            "model",
            "vehicle_type",
            "year",
            "mileage",
            "transmission",
            "fuel_type",
            "price",
            "description",
            "seller_phone",
            "is_commission",
            "view_count",
            "availability",
            "date_added",
            "images",
            "whatsapp_link",
            "absolute_url",
        )
        read_only_fields = ("id", "date_added", "images", "whatsapp_link", "absolute_url")

    def get_whatsapp_link(self, obj):
        return build_whatsapp_link()

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class PhoneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneImage
        fields = ("id", "phone", "image", "created_at")
        read_only_fields = ("id", "created_at")


class PhoneSerializer(serializers.ModelSerializer):
    images = PhoneImageSerializer(many=True, read_only=True)
    whatsapp_link = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = (
            "id",
            "slug",
            "brand",
            "model",
            "storage",
            "price",
            "description",
            "view_count",
            "availability",
            "date_added",
            "images",
            "whatsapp_link",
            "absolute_url",
        )
        read_only_fields = ("id", "date_added", "images", "whatsapp_link", "absolute_url")

    def get_whatsapp_link(self, obj):
        return build_whatsapp_link()

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class AccessorySerializer(serializers.ModelSerializer):
    whatsapp_link = serializers.SerializerMethodField()

    class Meta:
        model = Accessory
        fields = (
            "id",
            "name",
            "price",
            "description",
            "image",
            "availability",
            "date_added",
            "whatsapp_link",
        )
        read_only_fields = ("id", "date_added", "whatsapp_link")

    def get_whatsapp_link(self, obj):
        return build_whatsapp_link()


class RealEstateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealEstateImage
        fields = ("id", "real_estate", "image", "created_at")
        read_only_fields = ("id", "created_at")


class RealEstateSerializer(serializers.ModelSerializer):
    images = RealEstateImageSerializer(many=True, read_only=True)
    whatsapp_link = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = RealEstate
        fields = (
            "id",
            "slug",
            "real_estate_type",
            "location",
            "price",
            "description",
            "is_commission",
            "view_count",
            "availability",
            "date_added",
            "images",
            "whatsapp_link",
            "absolute_url",
        )
        read_only_fields = ("id", "date_added", "images", "whatsapp_link", "absolute_url")

    def get_whatsapp_link(self, obj):
        return build_whatsapp_link()

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()


class ProposalImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalImage
        fields = ("id", "proposal", "image", "created_at")
        read_only_fields = ("id", "created_at")


class ProposalSerializer(serializers.ModelSerializer):
    images = ProposalImageSerializer(many=True, read_only=True)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "name",
            "phone_number",
            "asset_type",
            "description",
            "desired_price",
            "created_at",
            "images",
        )
        read_only_fields = ("id", "created_at", "images")
