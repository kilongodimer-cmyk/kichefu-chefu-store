from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .forms import CarCSVImportForm
from .importers import CarCSVImporter
from .models import (
	Accessory,
	Car,
	CarImage,
	CarSellRequest,
	CarSellRequestImage,
	Favorite,
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
	change_list_template = "admin/marketplace/car/change_list.html"
	list_per_page = 50
	list_display = ("brand", "model", "vehicle_type", "year", "mileage", "price", "view_count", "is_commission", "availability", "date_added")
	list_filter = ("availability", "is_commission", "vehicle_type", "year", "brand", "fuel_type", "transmission")
	search_fields = ("brand", "model", "description")
	ordering = ("-date_added",)
	inlines = [CarImageInline]

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"import-csv/",
				self.admin_site.admin_view(self.import_csv_view),
				name="marketplace_car_import_csv",
			),
		]
		return custom_urls + urls

	def import_csv_view(self, request):
		if request.method == "POST":
			form = CarCSVImportForm(request.POST, request.FILES)
			if form.is_valid():
				importer = CarCSVImporter(duplicate_strategy=form.cleaned_data["duplicate_strategy"])
				result = importer.import_file(
					csv_file=form.cleaned_data["csv_file"],
					images_zip_file=form.cleaned_data.get("images_zip"),
				)

				if result.errors:
					messages.warning(
						request,
						f"Import termine avec erreurs: {len(result.errors)} ligne(s) ignoree(s).",
					)
					for error in result.errors[:20]:
						messages.error(request, error)
				else:
					messages.success(request, "Import termine sans erreur.")

				messages.info(
					request,
					(
						f"Traite: {result.processed} | Crees: {result.created} | "
						f"Mises a jour: {result.updated} | Doublons ignores: {result.skipped_duplicates} | "
						f"Images ajoutees: {result.images_added}"
					),
				)
				return redirect(reverse("admin:marketplace_car_changelist"))
		else:
			form = CarCSVImportForm()

		context = {
			**self.admin_site.each_context(request),
			"opts": self.model._meta,
			"title": "Importer des voitures via CSV",
			"form": form,
		}
		return render(request, "admin/marketplace/car/import_csv.html", context)


class PhoneImageInline(admin.TabularInline):
	model = PhoneImage
	extra = 1


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
	list_display = ("brand", "model", "storage", "price", "view_count", "availability", "date_added")
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
	list_display = ("real_estate_type", "location", "price", "view_count", "is_commission", "availability", "date_added")
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


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
	list_display = ("user", "content_type", "object_id", "created_at")
	list_filter = ("content_type", "created_at")
	search_fields = ("user__username",)
	ordering = ("-created_at",)

# Register your models here.
