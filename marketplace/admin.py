from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
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
	PriceDropAlert,
	Phone,
	PhoneImage,
	Proposal,
	ProposalImage,
	RealEstate,
	RealEstateImage,
	UserMarketplaceProfile,
	UserNotification,
)


admin.site.site_header = "Administration KICHEFU-CHEFU STORE"
admin.site.site_title = "Administration KICHEFU-CHEFU"
admin.site.index_title = "Pilotage du catalogue"


class CarImageInline(admin.TabularInline):
	model = CarImage
	extra = 1
	fields = ("image", "preview", "created_at")
	readonly_fields = ("preview", "created_at")

	def preview(self, obj):
		if obj and obj.image:
			return format_html('<img src="{}" style="height:72px;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
		return "-"

	preview.short_description = "Apercu"


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
				"<int:car_id>/publish/",
				self.admin_site.admin_view(self.publish_view),
				name="marketplace_car_publish",
			),
			path(
				"import-csv/",
				self.admin_site.admin_view(self.import_csv_view),
				name="marketplace_car_import_csv",
			),
		]
		return custom_urls + urls

	def publish_view(self, request, car_id):
		car = self.get_queryset(request).filter(pk=car_id).first()
		if not car:
			messages.error(request, "Annonce introuvable.")
			return redirect(reverse("admin:marketplace_car_changelist"))

		car.availability = "available"
		car.save(update_fields=["availability"])
		messages.success(request, "Annonce publiee.")
		return redirect(reverse("admin:marketplace_car_change", args=[car.pk]))

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
			"title": "Importer vehicules via CSV",
			"form": form,
		}
		return render(request, "admin/marketplace/car/import_csv.html", context)


class PhoneImageInline(admin.TabularInline):
	model = PhoneImage
	extra = 1
	fields = ("image", "preview", "created_at")
	readonly_fields = ("preview", "created_at")

	def preview(self, obj):
		if obj and obj.image:
			return format_html('<img src="{}" style="height:72px;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
		return "-"

	preview.short_description = "Apercu"


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
	list_display = ("brand", "model", "storage", "price", "view_count", "availability", "date_added")
	list_filter = ("availability", "brand")
	search_fields = ("brand", "model", "description")
	ordering = ("-date_added",)
	inlines = [PhoneImageInline]

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"<int:phone_id>/publish/",
				self.admin_site.admin_view(self.publish_view),
				name="marketplace_phone_publish",
			),
		]
		return custom_urls + urls

	def publish_view(self, request, phone_id):
		phone = self.get_queryset(request).filter(pk=phone_id).first()
		if not phone:
			messages.error(request, "Annonce introuvable.")
			return redirect(reverse("admin:marketplace_phone_changelist"))

		phone.availability = "available"
		phone.save(update_fields=["availability"])
		messages.success(request, "Annonce publiee.")
		return redirect(reverse("admin:marketplace_phone_change", args=[phone.pk]))


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
	list_display = ("name", "image_preview", "price", "availability", "date_added")
	list_filter = ("availability",)
	search_fields = ("name", "description")
	ordering = ("-date_added",)
	readonly_fields = ("image_preview",)

	def image_preview(self, obj):
		if obj and obj.image:
			return format_html('<img src="{}" style="height:72px;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
		return "-"

	image_preview.short_description = "Apercu"


class RealEstateImageInline(admin.TabularInline):
	model = RealEstateImage
	extra = 1
	fields = ("image", "preview", "created_at")
	readonly_fields = ("preview", "created_at")

	def preview(self, obj):
		if obj and obj.image:
			return format_html('<img src="{}" style="height:72px;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
		return "-"

	preview.short_description = "Apercu"


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
	fields = ("image", "preview", "created_at")
	readonly_fields = ("preview", "created_at")

	def preview(self, obj):
		if obj and obj.image:
			return format_html('<img src="{}" style="height:72px;border-radius:8px;border:1px solid #ddd;" />', obj.image.url)
		return "-"

	preview.short_description = "Apercu"


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
	list_display = ("name", "asset_type", "brand", "model_name", "city", "desired_price", "phone_number", "created_at")
	list_filter = ("asset_type", "created_at")
	search_fields = ("name", "phone_number", "brand", "model_name", "city", "location_details", "description")
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


@admin.register(PriceDropAlert)
class PriceDropAlertAdmin(admin.ModelAdmin):
	list_display = ("user", "content_type", "object_id", "target_price", "is_active", "created_at")
	list_filter = ("content_type", "is_active", "created_at")
	search_fields = ("user__username",)
	ordering = ("-created_at",)


@admin.register(UserMarketplaceProfile)
class UserMarketplaceProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "city", "notify_new_listings", "updated_at")
	list_filter = ("notify_new_listings", "city")
	search_fields = ("user__username", "city")
	ordering = ("-updated_at",)


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
	list_display = ("user", "notification_type", "title", "is_read", "created_at")
	list_filter = ("notification_type", "is_read", "created_at")
	search_fields = ("user__username", "title", "message")
	ordering = ("-created_at",)

# Register your models here.
