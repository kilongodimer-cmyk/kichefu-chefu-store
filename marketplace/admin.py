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
	Commission,
	Favorite,
	PriceDropAlert,
	Phone,
	PhoneImage,
	Product,
	Proposal,
	ProposalImage,
	RealEstate,
	RealEstateImage,
	Sale,
	SellerProfile,
	UserMarketplaceProfile,
	UserNotification,
	Video,
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("titre", "prix", "url_produit", "created_at")
	search_fields = ("titre", "description", "url_produit")
	ordering = ("-created_at",)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
	list_display = ("titre", "produit", "is_active", "created_at")
	list_filter = ("is_active", "created_at")
	search_fields = ("titre", "description", "produit__titre")
	autocomplete_fields = ("produit",)
	ordering = ("-created_at",)


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


# ──────────────────────────────────────────────────────────────
# SYSTÈME DE COMMISSION
# ──────────────────────────────────────────────────────────────


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
	list_display = ("display_name", "seller_type", "phone", "city", "commission_rate", "is_verified", "is_active", "created_at")
	list_filter = ("seller_type", "is_verified", "is_active", "city")
	search_fields = ("user__username", "business_name", "phone", "city")
	list_editable = ("commission_rate", "is_verified", "is_active")
	ordering = ("-created_at",)
	autocomplete_fields = ("user",)



class CommissionInline(admin.StackedInline):
	model = Commission
	extra = 0
	readonly_fields = ("rate", "amount", "created_at")
	fields = ("rate", "amount", "status", "paid_at", "created_at")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
	list_display = ("reference", "seller", "item_title", "sale_price", "commission_display", "payment_method", "created_at")
	list_filter = ("payment_method", "created_at", "seller__seller_type")
	search_fields = ("reference", "item_title", "seller__business_name", "buyer_name", "buyer_phone")
	date_hierarchy = "created_at"
	ordering = ("-created_at",)
	readonly_fields = ("reference",)
	inlines = [CommissionInline]
	autocomplete_fields = ("seller",)

	def commission_display(self, obj):
		try:
			c = obj.commission
			color = {"pending": "#e67e00", "paid": "#27ae60", "cancelled": "#999"}.get(c.status, "#333")
			return format_html('<span style="color:{};font-weight:bold">{} USD ({}%)</span>', color, c.amount, c.rate)
		except Commission.DoesNotExist:
			return "-"
	commission_display.short_description = "Commission"

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		if not change:
			Commission.create_for_sale(obj)


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
	list_display = ("sale", "rate", "amount", "status", "paid_at", "created_at")
	list_filter = ("status", "created_at")
	list_editable = ("status",)
	search_fields = ("sale__reference", "sale__item_title", "sale__seller__business_name")
	date_hierarchy = "created_at"
	ordering = ("-created_at",)
	actions = ["mark_as_paid"]

	@admin.action(description="Marquer comme payee")
	def mark_as_paid(self, request, queryset):
		from django.utils import timezone
		updated = queryset.filter(status=Commission.Status.PENDING).update(
			status=Commission.Status.PAID, paid_at=timezone.now()
		)
		self.message_user(request, f"{updated} commission(s) marquee(s) comme payee(s).", messages.SUCCESS)
