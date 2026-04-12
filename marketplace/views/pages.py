from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import F, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from ..forms import ProposalSellForm
from ..models import (
	Accessory,
	AvailabilityChoices,
	Car,
	CarImage,
	Favorite,
	PriceDropAlert,
	Phone,
	PhoneImage,
	Proposal,
	ProposalImage,
	RealEstate,
	RealEstateType,
	UserNotification,
	Video,
)
from .helpers import (
	LUBUMBASHI_NEIGHBORHOODS,
	WHATSAPP_DEFAULT,
	build_badges,
	build_proposal_whatsapp_message,
	build_smart_recommendations,
	get_favorite_id_map,
	get_recommended_from_history,
	get_user_city,
	make_whatsapp_link,
	publish_proposal_to_catalog,
	track_recent_view,
	_first_image_url,
	_normalize_price_filters,
	_serialize_car_cards,
)
from .auth import sanitize_next_url


class HomePageView(View):
	"""Construit la page vitrine en agrégeant statistiques, tendances et favoris."""
	template_name = "kichefu_store.html"

	def get(self, request):
		cars = Car.objects.prefetch_related("images").all()
		phones = Phone.objects.prefetch_related("images").all()
		accessories = Accessory.objects.all()
		real_estates = RealEstate.objects.prefetch_related("images").all()
		videos = Video.objects.select_related("produit").filter(is_active=True)[:12]
		user_city = get_user_city(request)
		available_cars_count = cars.filter(availability="available").count()

		popular_cars = list(cars.filter(availability="available")[:6])
		new_cars = list(cars.filter(date_added__gte=timezone.now() - timedelta(days=30))[:6])
		popular_phones = list(phones.filter(availability="available")[:6])
		recent_real_estates = list(real_estates.filter(location__in=LUBUMBASHI_NEIGHBORHOODS)[:6])
		hot_cars = list(cars.order_by("-view_count", "-date_added")[:6])
		hot_phones = list(phones.order_by("-view_count", "-date_added")[:6])
		hot_real_estate = list(real_estates.order_by("-view_count", "-date_added")[:6])

		latest_cars = list(cars.order_by("-date_added")[:4])
		latest_phones = list(phones.order_by("-date_added")[:4])
		latest_real_estate = list(real_estates.order_by("-date_added")[:4])
		most_viewed_items = []
		for car in cars.order_by("-view_count", "-date_added")[:4]:
			most_viewed_items.append({"kind": "Voiture", "title": f"{car.brand} {car.model}", "price": car.price, "url": car.get_absolute_url()})
		for phone in phones.order_by("-view_count", "-date_added")[:4]:
			most_viewed_items.append({"kind": "Telephone", "title": f"{phone.brand} {phone.model}", "price": phone.price, "url": phone.get_absolute_url()})
		for listing in real_estates.order_by("-view_count", "-date_added")[:4]:
			most_viewed_items.append(
				{
					"kind": "Immobilier",
					"title": f"{listing.get_real_estate_type_display()} - {listing.location}",
					"price": listing.price,
					"url": listing.get_absolute_url(),
				}
			)

		most_sold_items = []
		for car in cars.filter(availability="sold").order_by("-date_added")[:5]:
			most_sold_items.append({"kind": "Voiture", "title": f"{car.brand} {car.model}", "price": car.price, "url": car.get_absolute_url()})
		for phone in phones.filter(availability="sold").order_by("-date_added")[:5]:
			most_sold_items.append({"kind": "Telephone", "title": f"{phone.brand} {phone.model}", "price": phone.price, "url": phone.get_absolute_url()})
		for listing in real_estates.filter(availability="sold").order_by("-date_added")[:5]:
			most_sold_items.append(
				{
					"kind": "Immobilier",
					"title": f"{listing.get_real_estate_type_display()} - {listing.location}",
					"price": listing.price,
					"url": listing.get_absolute_url(),
				}
			)
		new_products = []
		for car in latest_cars:
			new_products.append({"kind": "Voiture", "title": f"{car.brand} {car.model}", "price": car.price, "url": car.get_absolute_url()})
		for phone in latest_phones:
			new_products.append({"kind": "Telephone", "title": f"{phone.brand} {phone.model}", "price": phone.price, "url": phone.get_absolute_url()})
		for listing in latest_real_estate:
			new_products.append(
				{
					"kind": "Immobilier",
					"title": f"{listing.get_real_estate_type_display()} - {listing.location}",
					"price": listing.price,
					"url": listing.get_absolute_url(),
				}
			)
		new_products = sorted(new_products, key=lambda item: item["price"])[:12]

		nearby_cars = []
		if user_city:
			nearby_cars = list(cars.filter(city__iexact=user_city, availability="available").order_by("-view_count", "-date_added")[:8])

		best_offers = []
		for car in cars.filter(availability="available").order_by("price")[:4]:
			best_offers.append({"kind": "Voiture", "title": f"{car.brand} {car.model}", "price": car.price, "url": car.get_absolute_url()})
		for phone in phones.filter(availability="available").order_by("price")[:4]:
			best_offers.append({"kind": "Telephone", "title": f"{phone.brand} {phone.model}", "price": phone.price, "url": phone.get_absolute_url()})
		for listing in real_estates.filter(availability="available").order_by("price")[:4]:
			best_offers.append(
				{
					"kind": "Immobilier",
					"title": f"{listing.get_real_estate_type_display()} a {listing.location}",
					"price": listing.price,
					"url": listing.get_absolute_url(),
				}
			)
		best_offers = sorted(best_offers, key=lambda x: x["price"])[:8]
		recommended_for_you = get_recommended_from_history(request)
		favorite_map = get_favorite_id_map(request.user)

		context = {
			"popular_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(popular_cars)],
			"new_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(new_cars)],
			"popular_phones": [(item, build_badges(item, idx)) for idx, item in enumerate(popular_phones)],
			"top_accessories": [(item, build_badges(item, idx)) for idx, item in enumerate(accessories.filter(availability="available")[:6])],
			"recent_real_estates": [(item, build_badges(item, idx)) for idx, item in enumerate(recent_real_estates)],
			"best_offers": best_offers,
			"popular_products": {
				"cars": [(item, build_badges(item, idx)) for idx, item in enumerate(hot_cars)],
				"phones": [(item, build_badges(item, idx)) for idx, item in enumerate(hot_phones)],
				"real_estate": [(item, build_badges(item, idx)) for idx, item in enumerate(hot_real_estate)],
			},
			"recommended_for_you": recommended_for_you,
			"most_viewed_items": most_viewed_items[:10],
			"most_sold_items": most_sold_items[:10],
			"new_products": new_products,
			"nearby_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(nearby_cars)],
			"user_city": user_city,
			"available_cars_count": available_cars_count,
			"favorite_car_ids": favorite_map["cars"],
			"favorite_phone_ids": favorite_map["phones"],
			"favorite_real_estate_ids": favorite_map["real_estate"],
			"lubumbashi_areas": LUBUMBASHI_NEIGHBORHOODS,
			"spotlight_videos": videos,
		}
		return render(request, self.template_name, context)


class SearchSuggestionsView(View):
	"""Retourne des suggestions rapides (JSON) pour l'autocomplétion globale."""
	def get(self, request):
		query = request.GET.get("q", "").strip()
		if len(query) < 2:
			return JsonResponse({"suggestions": []})

		suggestions = []

		cars = Car.objects.filter(Q(brand__icontains=query) | Q(model__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in cars:
			suggestions.append({"title": f"{item.brand} {item.model}", "category": "Voiture", "url": item.get_absolute_url()})

		phones = Phone.objects.filter(Q(brand__icontains=query) | Q(model__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in phones:
			suggestions.append({"title": f"{item.brand} {item.model}", "category": "Telephone", "url": item.get_absolute_url()})

		estates = RealEstate.objects.filter(Q(location__icontains=query) | Q(description__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in estates:
			suggestions.append({"title": f"{item.get_real_estate_type_display()} {item.location}", "category": "Parcelle/Maison", "url": item.get_absolute_url()})

		return JsonResponse({"suggestions": suggestions[:10]})


class GlobalSearchView(View):
	template_name = "search_results.html"

	def get(self, request):
		"""Exécute une recherche multi-catégories avec filtres dynamiques."""
		query = request.GET.get("q", "").strip()
		category = request.GET.get("category", "all").strip() or "all"
		brand = request.GET.get("brand", "").strip()
		model = request.GET.get("model", "").strip()
		neighborhood = request.GET.get("neighborhood", "").strip()
		min_price, max_price = _normalize_price_filters(request)

		results = []
		approximate_used = False

		if category in {"all", "cars"}:
			cars = Car.objects.prefetch_related("images").all()
			if query:
				cars = cars.filter(Q(brand__icontains=query) | Q(model__icontains=query) | Q(description__icontains=query))
			if brand:
				cars = cars.filter(brand__icontains=brand)
			if model:
				cars = cars.filter(model__icontains=model)
			if min_price is not None:
				cars = cars.filter(price__gte=min_price)
			if max_price is not None:
				cars = cars.filter(price__lte=max_price)
			for item in cars.order_by("-view_count", "-date_added")[:80]:
				results.append(
					{
						"category": "Voiture",
						"title": f"{item.brand} {item.model}",
						"price": item.price,
						"url": item.get_absolute_url(),
						"image_url": _first_image_url(item),
					}
				)

		if category in {"all", "phones"}:
			phones = Phone.objects.prefetch_related("images").all()
			if query:
				phones = phones.filter(Q(brand__icontains=query) | Q(model__icontains=query) | Q(description__icontains=query))
			if brand:
				phones = phones.filter(brand__icontains=brand)
			if model:
				phones = phones.filter(model__icontains=model)
			if min_price is not None:
				phones = phones.filter(price__gte=min_price)
			if max_price is not None:
				phones = phones.filter(price__lte=max_price)
			for item in phones.order_by("-view_count", "-date_added")[:80]:
				results.append(
					{
						"category": "Telephone",
						"title": f"{item.brand} {item.model}",
						"price": item.price,
						"url": item.get_absolute_url(),
						"image_url": _first_image_url(item),
					}
				)

		if category in {"all", "real-estate"}:
			estates = RealEstate.objects.prefetch_related("images").all()
			if query:
				estates = estates.filter(Q(location__icontains=query) | Q(description__icontains=query))
			if neighborhood:
				estates = estates.filter(location__icontains=neighborhood)
			if min_price is not None:
				estates = estates.filter(price__gte=min_price)
			if max_price is not None:
				estates = estates.filter(price__lte=max_price)
			for item in estates.order_by("-view_count", "-date_added")[:80]:
				results.append(
					{
						"category": item.get_real_estate_type_display(),
						"title": f"{item.get_real_estate_type_display()} - {item.location}",
						"price": item.price,
						"url": item.get_absolute_url(),
						"image_url": _first_image_url(item),
					}
				)

		if not results and query:
			approximate_results = []
			prefix = query.split()[0]
			if prefix:
				approx_cars = (
					Car.objects.prefetch_related("images")
					.filter(Q(brand__istartswith=prefix) | Q(model__istartswith=prefix))
					.order_by("-view_count", "-date_added")[:6]
				)
				for item in approx_cars:
					approximate_results.append({"category": "Voiture", "title": f"{item.brand} {item.model}", "price": item.price, "url": item.get_absolute_url(), "image_url": _first_image_url(item)})

				approx_phones = (
					Phone.objects.prefetch_related("images")
					.filter(Q(brand__istartswith=prefix) | Q(model__istartswith=prefix))
					.order_by("-view_count", "-date_added")[:6]
				)
				for item in approx_phones:
					approximate_results.append({"category": "Telephone", "title": f"{item.brand} {item.model}", "price": item.price, "url": item.get_absolute_url(), "image_url": _first_image_url(item)})

				approx_estates = (
					RealEstate.objects.prefetch_related("images")
					.filter(Q(location__istartswith=prefix))
					.order_by("-view_count", "-date_added")[:6]
				)
				for item in approx_estates:
					approximate_results.append({"category": item.get_real_estate_type_display(), "title": f"{item.get_real_estate_type_display()} - {item.location}", "price": item.price, "url": item.get_absolute_url(), "image_url": _first_image_url(item)})

			if approximate_results:
				results = approximate_results
				approximate_used = True

		results.sort(key=lambda result: result["price"])

		paginator = Paginator(results, 18)
		page_obj = paginator.get_page(request.GET.get("page", 1))

		context = {
			"page_obj": page_obj,
			"total_results": len(results),
			"approximate_used": approximate_used,
			"filters": {
				"q": query,
				"category": category,
				"brand": brand,
				"model": model,
				"neighborhood": neighborhood,
				"min_price": request.GET.get("min_price", "").strip(),
				"max_price": request.GET.get("max_price", "").strip(),
			},
		}
		return render(request, self.template_name, context)


class CarMarketplaceListView(View):
	"""Page de listing voitures avec filtres avancés et export JSON pour l'UI."""
	template_name = "cars_marketplace.html"

	def get(self, request):
		user_city = get_user_city(request)
		image_queryset = CarImage.objects.only("id", "car_id", "image", "created_at").order_by("-created_at")
		cars = (
			Car.objects.only(
				"id", "brand", "model", "slug", "vehicle_type", "year", "mileage",
				"fuel_type", "transmission", "price", "city", "is_commission",
				"availability", "view_count", "date_added",
			)
			.prefetch_related(Prefetch("images", queryset=image_queryset))
			.order_by("-date_added")
		)

		search = request.GET.get("q", "").strip()
		brand = request.GET.get("brand", "").strip()
		vehicle_type = request.GET.get("vehicle_type", "").strip()
		year = request.GET.get("year", "").strip()
		max_mileage = request.GET.get("max_mileage", "").strip()
		fuel_type = request.GET.get("fuel_type", "").strip()
		transmission = request.GET.get("transmission", "").strip()
		city = request.GET.get("city", "").strip() or user_city
		min_price = request.GET.get("min_price", "").strip()
		max_price = request.GET.get("max_price", "").strip()

		if search:
			cars = cars.filter(Q(brand__icontains=search) | Q(model__icontains=search))
		if brand:
			cars = cars.filter(brand__iexact=brand)
		if vehicle_type:
			cars = cars.filter(vehicle_type=vehicle_type)
		if year.isdigit():
			cars = cars.filter(year=int(year))
		if max_mileage.isdigit():
			cars = cars.filter(mileage__lte=int(max_mileage))
		if fuel_type:
			cars = cars.filter(fuel_type=fuel_type)
		if transmission:
			cars = cars.filter(transmission=transmission)
		if city:
			cars = cars.filter(city__icontains=city)

		try:
			if min_price:
				cars = cars.filter(price__gte=float(min_price))
			if max_price:
				cars = cars.filter(price__lte=float(max_price))
		except ValueError:
			pass

		paginator = Paginator(cars, 12)
		page_obj = paginator.get_page(request.GET.get("page", 1))
		favorite_ids = get_favorite_id_map(request.user)["cars"]

		if request.GET.get("format") == "json":
			return JsonResponse(
				{
					"results": _serialize_car_cards(page_obj.object_list, request, favorite_ids=favorite_ids),
					"page": page_obj.number,
					"has_next": page_obj.has_next(),
					"next_page": page_obj.next_page_number() if page_obj.has_next() else None,
				}
			)

		nearby_cars = []
		if user_city:
			nearby_cars = list(
				cars.filter(city__iexact=user_city)
				.exclude(pk__in=[item.pk for item in page_obj.object_list])
				.order_by("-view_count", "-date_added")[:6]
			)

		context = {
			"page_obj": page_obj,
			"brands": Car.objects.values_list("brand", flat=True).distinct().order_by("brand"),
			"vehicle_types": Car.VehicleType.choices,
			"fuel_types": Car.FuelType.choices,
			"transmission_types": Car.TransmissionType.choices,
			"car_items": [(item, build_badges(item, idx)) for idx, item in enumerate(page_obj.object_list)],
			"favorite_car_ids": favorite_ids,
			"nearby_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(nearby_cars)],
			"user_city": user_city,
			"filters": {
				"q": search, "brand": brand, "vehicle_type": vehicle_type, "year": year,
				"max_mileage": max_mileage, "fuel_type": fuel_type, "transmission": transmission,
				"city": city, "min_price": min_price, "max_price": max_price,
			},
		}
		return render(request, self.template_name, context)


class CarDetailView(View):
	"""Fiche détaillée voiture : comptabilise la vue et calcule les recommandations."""
	template_name = "car_detail.html"

	def get(self, request, slug):
		car_queryset = Car.objects.prefetch_related("images")
		car = car_queryset.filter(slug=slug).first()
		if car is None and str(slug).isdigit():
			legacy_car = car_queryset.filter(pk=int(slug)).first()
			if legacy_car:
				return redirect(legacy_car.get_absolute_url())
		car = get_object_or_404(car_queryset, slug=slug)
		Car.objects.filter(pk=car.pk).update(view_count=F("view_count") + 1)
		car.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "cars", car.pk)
		favorite_map = get_favorite_id_map(request.user)
		user_city = get_user_city(request)
		contact_phone = car.seller_phone or WHATSAPP_DEFAULT
		whatsapp_message = f"Bonjour, je suis interesse par {car.brand} {car.model} sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(contact_phone, whatsapp_message)
		car_base_queryset = Car.objects.prefetch_related("images").all()
		reco = build_smart_recommendations(
			base_queryset=car_base_queryset,
			item=car,
			category_filters={"vehicle_type": car.vehicle_type},
			brand_filter_key="brand",
			location_filter_key="city__iexact",
			location_value=car.city or user_city,
		)
		car_alert_active = False
		if request.user.is_authenticated:
			car_alert_active = PriceDropAlert.objects.filter(
				user=request.user,
				content_type=ContentType.objects.get_for_model(Car),
				object_id=car.pk,
				is_active=True,
			).exists()

		return render(
			request,
			self.template_name,
			{
				"car": car,
				"contact_phone": contact_phone,
				"whatsapp_link": whatsapp_link,
				"is_favorite": car.pk in favorite_map["cars"],
				"price_alert_active": car_alert_active,
				"similar_cars": reco["similar"],
				"same_price_cars": reco["same_price"],
				"popular_today_cars": reco["popular_today"],
				"new_arrivals_cars": reco["new_arrivals"],
				"recommended_cars": reco["you_might_like"],
			},
		)


class PhoneMarketplaceListView(View):
	"""Catalogue téléphones avec tri prix/marque pour la page /telephones/."""
	template_name = "phones_marketplace.html"

	def get(self, request):
		phones = Phone.objects.prefetch_related("images").all()

		search = request.GET.get("q", "").strip()
		brand = request.GET.get("brand", "").strip()
		min_price = request.GET.get("min_price", "").strip()
		max_price = request.GET.get("max_price", "").strip()

		if search:
			phones = phones.filter(Q(brand__icontains=search) | Q(model__icontains=search))
		if brand:
			phones = phones.filter(brand__iexact=brand)
		try:
			if min_price:
				phones = phones.filter(price__gte=float(min_price))
			if max_price:
				phones = phones.filter(price__lte=float(max_price))
		except ValueError:
			pass

		paginator = Paginator(phones, 12)
		page_obj = paginator.get_page(request.GET.get("page", 1))

		context = {
			"page_obj": page_obj,
			"phone_items": [(item, build_badges(item, idx)) for idx, item in enumerate(page_obj.object_list)],
			"favorite_phone_ids": get_favorite_id_map(request.user)["phones"],
			"brands": Phone.objects.values_list("brand", flat=True).distinct().order_by("brand"),
			"filters": {"q": search, "brand": brand, "min_price": min_price, "max_price": max_price},
		}
		return render(request, self.template_name, context)


class PhoneDetailView(View):
	"""Affiche une fiche téléphone et active les recommandations liées (stockage/marque)."""
	template_name = "phone_detail.html"

	def get(self, request, slug):
		phone_queryset = Phone.objects.prefetch_related("images")
		phone = phone_queryset.filter(slug=slug).first()
		if phone is None and str(slug).isdigit():
			legacy_phone = phone_queryset.filter(pk=int(slug)).first()
			if legacy_phone:
				return redirect(legacy_phone.get_absolute_url())
		phone = get_object_or_404(phone_queryset, slug=slug)
		Phone.objects.filter(pk=phone.pk).update(view_count=F("view_count") + 1)
		phone.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "phones", phone.pk)
		favorite_map = get_favorite_id_map(request.user)
		whatsapp_message = f"Bonjour, je veux le {phone.brand} {phone.model} vu sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		phone_base_queryset = Phone.objects.prefetch_related("images").all()
		reco = build_smart_recommendations(
			base_queryset=phone_base_queryset,
			item=phone,
			category_filters={"storage": phone.storage},
			brand_filter_key="brand",
		)
		phone_alert_active = False
		if request.user.is_authenticated:
			phone_alert_active = PriceDropAlert.objects.filter(
				user=request.user,
				content_type=ContentType.objects.get_for_model(Phone),
				object_id=phone.pk,
				is_active=True,
			).exists()
		return render(
			request,
			self.template_name,
			{
				"phone": phone,
				"whatsapp_link": whatsapp_link,
				"is_favorite": phone.pk in favorite_map["phones"],
				"price_alert_active": phone_alert_active,
				"similar_phones": reco["similar"],
				"same_price_phones": reco["same_price"],
				"popular_today_phones": reco["popular_today"],
				"new_arrivals_phones": reco["new_arrivals"],
				"recommended_phones": reco["you_might_like"],
			},
		)


class AccessoryMarketplaceListView(View):
	"""Mini marketplace accessoires avec pagination simple et recherche libre."""
	template_name = "accessories_marketplace.html"

	def get(self, request):
		items = Accessory.objects.all()
		search = request.GET.get("q", "").strip()
		if search:
			items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))

		paginator = Paginator(items, 16)
		page_obj = paginator.get_page(request.GET.get("page", 1))
		context = {
			"page_obj": page_obj,
			"accessory_items": [(item, build_badges(item, idx)) for idx, item in enumerate(page_obj.object_list)],
			"filters": {"q": search},
		}
		return render(request, self.template_name, context)


class AccessoryDetailView(View):
	template_name = "accessory_detail.html"

	def get(self, request, pk):
		accessory = get_object_or_404(Accessory, pk=pk)
		whatsapp_message = f"Bonjour, je suis interesse par l'accessoire {accessory.name} sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		related_items = (
			Accessory.objects.filter(availability=AvailabilityChoices.AVAILABLE)
			.exclude(pk=accessory.pk)
			.order_by("-date_added")[:8]
		)
		return render(request, self.template_name, {"accessory": accessory, "whatsapp_link": whatsapp_link, "related_items": related_items})


class RealEstateMarketplaceListView(View):
	"""Listing immobilier avec filtres par type, quartier et recherche libre."""
	template_name = "real_estate_marketplace.html"

	def get(self, request):
		listings = RealEstate.objects.prefetch_related("images").all()

		estate_type = request.GET.get("real_estate_type", "").strip()
		location = request.GET.get("location", "").strip()
		search = request.GET.get("q", "").strip()

		if estate_type:
			listings = listings.filter(real_estate_type=estate_type)
		if location:
			listings = listings.filter(location__iexact=location)
		if search:
			listings = listings.filter(Q(location__icontains=search) | Q(description__icontains=search))

		paginator = Paginator(listings, 12)
		page_obj = paginator.get_page(request.GET.get("page", 1))
		context = {
			"page_obj": page_obj,
			"estate_items": [(item, build_badges(item, idx)) for idx, item in enumerate(page_obj.object_list)],
			"favorite_real_estate_ids": get_favorite_id_map(request.user)["real_estate"],
			"estate_types": RealEstate._meta.get_field("real_estate_type").choices,
			"lubumbashi_areas": LUBUMBASHI_NEIGHBORHOODS,
			"filters": {"real_estate_type": estate_type, "location": location, "q": search},
		}
		return render(request, self.template_name, context)


class RealEstateDetailView(View):
	"""Fiche immobilier : incrémente les vues et génère des blocs similaires/prix."""
	template_name = "real_estate_detail.html"

	def get(self, request, slug):
		listing_queryset = RealEstate.objects.prefetch_related("images")
		listing = listing_queryset.filter(slug=slug).first()
		if listing is None and str(slug).isdigit():
			legacy_listing = listing_queryset.filter(pk=int(slug)).first()
			if legacy_listing:
				return redirect(legacy_listing.get_absolute_url())
		listing = get_object_or_404(listing_queryset, slug=slug)
		RealEstate.objects.filter(pk=listing.pk).update(view_count=F("view_count") + 1)
		listing.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "real_estate", listing.pk)
		favorite_map = get_favorite_id_map(request.user)
		whatsapp_message = (
			f"Bonjour, je suis interesse par cette annonce {listing.get_real_estate_type_display()} a {listing.location}."
		)
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		real_estate_base_queryset = RealEstate.objects.prefetch_related("images").all()
		reco = build_smart_recommendations(
			base_queryset=real_estate_base_queryset,
			item=listing,
			category_filters={"real_estate_type": listing.real_estate_type},
			location_filter_key="location__iexact",
			location_value=listing.location,
		)
		listing_alert_active = False
		if request.user.is_authenticated:
			listing_alert_active = PriceDropAlert.objects.filter(
				user=request.user,
				content_type=ContentType.objects.get_for_model(RealEstate),
				object_id=listing.pk,
				is_active=True,
			).exists()
		return render(
			request,
			self.template_name,
			{
				"listing": listing,
				"whatsapp_link": whatsapp_link,
				"is_favorite": listing.pk in favorite_map["real_estate"],
				"price_alert_active": listing_alert_active,
				"similar_listings": reco["similar"],
				"same_price_listings": reco["same_price"],
				"popular_today_listings": reco["popular_today"],
				"new_arrivals_listings": reco["new_arrivals"],
				"recommended_listings": reco["you_might_like"],
			},
		)


class ToggleFavoriteView(LoginRequiredMixin, View):
	"""Ajoute/enlève un produit (voiture/tel/immobilier) du panier-favoris."""
	login_url = "/connexion/"

	def post(self, request, model_name, pk):
		model_map = {"car": Car, "phone": Phone, "real_estate": RealEstate}
		model_class = model_map.get(model_name)
		if model_class is None:
			return redirect("home")

		object_instance = get_object_or_404(model_class, pk=pk)
		if model_name == "phone":
			if (
				getattr(object_instance, "availability", "") == AvailabilityChoices.OUT_OF_STOCK
				or getattr(object_instance, "stock", 1) == 0
			):
				messages.error(request, "Produit en rupture de stock.")
				next_url = sanitize_next_url(request, request.POST.get("next", ""))
				return redirect(next_url or object_instance.get_absolute_url())
		content_type = ContentType.objects.get_for_model(model_class)
		favorite, created = Favorite.objects.get_or_create(
			user=request.user,
			content_type=content_type,
			object_id=object_instance.pk,
		)
		if not created:
			favorite.delete()

		next_url = sanitize_next_url(request, request.POST.get("next", ""))
		if next_url:
			return redirect(next_url)
		return redirect("home")


class FavoritesView(LoginRequiredMixin, View):
	"""Page panier : permet suppression groupée ou visualisation des favoris."""
	login_url = "/connexion/"
	template_name = "favorites.html"

	def post(self, request):
		selected_items = request.POST.getlist("selected_items")
		if not selected_items:
			messages.info(request, "Selectionnez au moins un element du panier a supprimer.")
			return redirect("marketplace:cart")

		model_map = {"car": Car, "phone": Phone, "real_estate": RealEstate}
		ids_by_model = {"car": set(), "phone": set(), "real_estate": set()}

		for token in selected_items:
			parts = token.split(":", 1)
			if len(parts) != 2:
				continue
			model_name, object_id = parts
			if model_name not in model_map:
				continue
			if not object_id.isdigit():
				continue
			ids_by_model[model_name].add(int(object_id))

		removed_count = 0
		for model_name, object_ids in ids_by_model.items():
			if not object_ids:
				continue
			content_type = ContentType.objects.get_for_model(model_map[model_name])
			deleted, _ = Favorite.objects.filter(
				user=request.user,
				content_type=content_type,
				object_id__in=list(object_ids),
			).delete()
			removed_count += deleted

		if removed_count:
			messages.success(request, f"{removed_count} element(s) retire(s) du panier.")
		else:
			messages.info(request, "Aucun element du panier n'a ete supprime.")

		return redirect("marketplace:cart")

	def get(self, request):
		favorite_map = get_favorite_id_map(request.user)
		cars = Car.objects.prefetch_related("images").filter(pk__in=favorite_map["cars"])
		phones = Phone.objects.prefetch_related("images").filter(pk__in=favorite_map["phones"])
		real_estates = RealEstate.objects.prefetch_related("images").filter(pk__in=favorite_map["real_estate"])
		return render(request, self.template_name, {"cars": cars, "phones": phones, "real_estates": real_estates})


class TogglePriceAlertView(LoginRequiredMixin, View):
	"""Active/désactive une alerte de prix sur un objet donné (tous catalogues)."""
	login_url = "/connexion/"

	def post(self, request, model_name, pk):
		model_map = {"car": Car, "phone": Phone, "real_estate": RealEstate}
		model_class = model_map.get(model_name)
		if model_class is None:
			return redirect("home")

		instance = get_object_or_404(model_class, pk=pk)
		content_type = ContentType.objects.get_for_model(model_class)
		target_price = request.POST.get("target_price", "").strip()
		try:
			alert_price = Decimal(target_price) if target_price else instance.price
		except (InvalidOperation, ValueError, TypeError):
			alert_price = instance.price

		alert, created = PriceDropAlert.objects.get_or_create(
			user=request.user,
			content_type=content_type,
			object_id=instance.pk,
			defaults={"target_price": alert_price, "is_active": True},
		)
		if not created:
			if alert.is_active:
				alert.is_active = False
				alert.save(update_fields=["is_active"])
				messages.info(request, "Alerte de prix desactivee.")
			else:
				alert.is_active = True
				alert.target_price = alert_price
				alert.save(update_fields=["is_active", "target_price"])
				messages.success(request, "Alerte de prix activee.")
		else:
			messages.success(request, "Alerte de prix activee.")

		next_url = sanitize_next_url(request, request.POST.get("next") or request.GET.get("next"))
		if next_url:
			return redirect(next_url)
		return redirect(instance.get_absolute_url())


class NotificationsView(LoginRequiredMixin, View):
	login_url = "/connexion/"
	template_name = "notifications.html"

	def post(self, request):
		if request.POST.get("mark_read") == "1":
			UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
		return redirect("marketplace:notifications")

	def get(self, request):
		notifications = UserNotification.objects.filter(user=request.user).order_by("-created_at")
		return render(request, self.template_name, {"notifications": notifications[:100]})


class SellWithUsView(View):
	template_name = "sell_with_us.html"

	def get(self, request):
		return render(request, self.template_name, {"form": ProposalSellForm()})

	def post(self, request):
		form = ProposalSellForm(request.POST, request.FILES)
		if not form.is_valid():
			return render(request, self.template_name, {"form": form})

		photos = form.cleaned_data.get("photos") or []
		proposal = form.save()
		image_urls = []
		for image in photos:
			proposal_image = ProposalImage.objects.create(proposal=proposal, image=image)
			if proposal_image.image:
				image_urls.append(request.build_absolute_uri(proposal_image.image.url))

		auto_publish_enabled = getattr(settings, "MARKETPLACE_AUTO_PUBLISH_PROPOSALS", False)
		created_listing = publish_proposal_to_catalog(proposal) if auto_publish_enabled else None
		if created_listing:
			listing_url = request.build_absolute_uri(created_listing.get_absolute_url())
			image_urls.append(listing_url)

		whatsapp_message = build_proposal_whatsapp_message(proposal, image_urls=image_urls)
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		return redirect(whatsapp_link)


class AgentDashboardView(LoginRequiredMixin, View):
	template_name = "agent/dashboard.html"
	login_url = "/agent/connexion/"

	def get(self, request):
		if not request.user.is_staff:
			messages.error(request, "Cet espace est reserve aux agents du site.")
			return redirect("home")

		is_admin_role = bool(
			request.user.is_superuser
			or request.user.groups.filter(name="Admin").exists()
		)

		context = {
			"cars_count": Car.objects.count(),
			"phones_count": Phone.objects.count(),
			"accessories_count": Accessory.objects.count(),
			"real_estate_count": RealEstate.objects.count(),
			"is_admin_role": is_admin_role,
		}
		return render(request, self.template_name, context)
