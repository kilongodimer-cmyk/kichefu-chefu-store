from django.contrib import admin

from .models import (
	Accessory,
	Car,
	CarImage,
	CarSellRequest,
	CarSellRequestImage,
	Phone,
	PhoneImage,
	Proposal,
	ProposalImage,
	RealEstate,
	RealEstateImage,
)


class CarImageInline(admin.TabularInline):
	model = CarImage
	extra = 1


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
	list_display = ("brand", "model", "vehicle_type", "year", "mileage", "price", "is_commission", "availability", "date_added")
	list_filter = ("availability", "is_commission", "vehicle_type", "year", "brand", "fuel_type", "transmission")
	search_fields = ("brand", "model", "description")
	ordering = ("-date_added",)
	inlines = [CarImageInline]


class PhoneImageInline(admin.TabularInline):
	model = PhoneImage
	extra = 1


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
	list_display = ("brand", "model", "storage", "price", "availability", "date_added")
	list_filter = ("availability", "brand")
	search_fields = ("brand", "model", "description")
	ordering = ("-date_added",)
	inlines = [PhoneImageInline]


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "availability", "date_added")
	list_filter = ("availability",)
	search_fields = ("name", "description")
	ordering = ("-date_added",)


class RealEstateImageInline(admin.TabularInline):
	model = RealEstateImage
	extra = 1


@admin.register(RealEstate)
class RealEstateAdmin(admin.ModelAdmin):
	list_display = ("real_estate_type", "location", "price", "is_commission", "availability", "date_added")
	list_filter = ("real_estate_type", "is_commission", "availability")
	search_fields = ("location", "description")
	ordering = ("-date_added",)
	inlines = [RealEstateImageInline]


class ProposalImageInline(admin.TabularInline):
	model = ProposalImage
	extra = 1


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
	list_display = ("name", "asset_type", "desired_price", "phone_number", "created_at")
	list_filter = ("asset_type", "created_at")
	search_fields = ("name", "phone_number", "description")
	ordering = ("-created_at",)
	inlines = [ProposalImageInline]


class CarSellRequestImageInline(admin.TabularInline):
	model = CarSellRequestImage
	extra = 1


@admin.register(CarSellRequest)
class CarSellRequestAdmin(admin.ModelAdmin):
	list_display = ("name", "phone_number", "model", "year", "desired_price", "created_at")
	list_filter = ("year", "created_at")
	search_fields = ("name", "phone_number", "model")
	ordering = ("-created_at",)
	inlines = [CarSellRequestImageInline]

# Register your models here.
