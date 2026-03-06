import re
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import F, Prefetch, Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from urllib.parse import quote
from datetime import timedelta
from decimal import Decimal

from .demo_seed import ensure_seeded_data
from .forms import ProposalSellForm
from .models import (
	Accessory,
	Car,
	CarImage,
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
from .permissions import ProposalPermission
from .serializers import (
	AccessorySerializer,
	CarImageSerializer,
	CarSerializer,
	PhoneImageSerializer,
	PhoneSerializer,
	ProposalImageSerializer,
	ProposalSerializer,
	RealEstateImageSerializer,
	RealEstateSerializer,
)


WHATSAPP_DEFAULT = "+243000000000"
LUBUMBASHI_NEIGHBORHOODS = ["Kenya", "Kamalondo", "Katuba", "Ruashi", "Golf", "Bel-Air", "Kalubwe"]
RECENT_SESSION_KEY = "recently_viewed"
USER_CITY_SESSION_KEY = "user_city"


def ensure_seeded_data_safe():
	try:
		ensure_seeded_data()
	except Exception:
		# Never block page/API rendering if DB is not ready yet.
		pass


def make_whatsapp_link(phone_number, message):
	number = (phone_number or WHATSAPP_DEFAULT).replace("+", "").replace(" ", "")
	return f"https://wa.me/{number}?text={quote(message)}"


def build_badges(item, index=0):
	badges = []
	if item.date_added >= timezone.now() - timedelta(days=21):
		badges.append("Nouveau")
	if index < 3:
		badges.append("Populaire")
	if str(getattr(item, "availability", "")) == "reserved":
		badges.append("Stock limite")
	if str(getattr(item, "availability", "")) == "available" and index % 4 == 0:
		badges.append("Bonne affaire")
	return badges


def _price_range(item):
	return item.price * Decimal("0.20")


def _collect_unique_candidates(tier_querysets, max_items=6):
	collected = []
	seen_ids = set()
	for queryset in tier_querysets:
		for obj in queryset:
			if obj.pk in seen_ids:
				continue
			collected.append(obj)
			seen_ids.add(obj.pk)
			if len(collected) >= max_items:
				return collected
	return collected


def similar_items_by_rules(base_queryset, item, tier_filters, min_items=4, max_items=6):
	price_delta = _price_range(item)
	price_filter = {
		"price__gte": item.price - price_delta,
		"price__lte": item.price + price_delta,
	}

	tier_querysets = []
	for filters_map in tier_filters:
		queryset = (
			base_queryset
			.exclude(pk=item.pk)
			.filter(**filters_map)
			.filter(**price_filter)
			.order_by("-view_count", "-date_added")[:max_items]
		)
		tier_querysets.append(queryset)

	if tier_filters:
		strict_queryset = (
			base_queryset
			.exclude(pk=item.pk)
			.filter(**tier_filters[0])
			.order_by("-view_count", "-date_added")[:max_items]
		)
		tier_querysets.append(strict_queryset)

	items = _collect_unique_candidates(tier_querysets=tier_querysets, max_items=max_items)

	if len(items) < min_items:
		fallback_queryset = (
			base_queryset
			.exclude(pk=item.pk)
			.exclude(pk__in=[candidate.pk for candidate in items])
			.order_by("-view_count", "-date_added")[:max_items]
		)
		items.extend(_collect_unique_candidates([fallback_queryset], max_items=max_items - len(items)))

	return items[:max_items]


def recommended_items_for_you(base_queryset, item, category_filters, min_items=4, max_items=6):
	category_queryset = base_queryset.exclude(pk=item.pk).filter(**category_filters)

	popular_in_category = category_queryset.order_by("-view_count", "-date_added")[:max_items]
	recent_in_category = category_queryset.order_by("-date_added")[:max_items]
	popular_global = base_queryset.exclude(pk=item.pk).order_by("-view_count", "-date_added")[:max_items]
	recent_global = base_queryset.exclude(pk=item.pk).order_by("-date_added")[:max_items]

	items = _collect_unique_candidates(
		tier_querysets=[popular_in_category, recent_in_category, popular_global, recent_global],
		max_items=max_items,
	)

	if len(items) < min_items:
		fallback_queryset = (
			base_queryset
			.exclude(pk=item.pk)
			.exclude(pk__in=[candidate.pk for candidate in items])
			.order_by("-view_count", "-date_added")[:max_items]
		)
		items.extend(_collect_unique_candidates([fallback_queryset], max_items=max_items - len(items)))

	return items[:max_items]


def build_smart_recommendations(
	base_queryset,
	item,
	category_filters,
	brand_filter_key=None,
	location_filter_key=None,
	location_value=None,
	max_items=6,
):
	price_delta = _price_range(item)
	price_filter = {
		"price__gte": item.price - price_delta,
		"price__lte": item.price + price_delta,
	}

	tier_filters = [dict(category_filters)]
	if brand_filter_key and hasattr(item, brand_filter_key):
		brand_value = getattr(item, brand_filter_key)
		if brand_value:
			brand_map = dict(category_filters)
			brand_map[brand_filter_key] = brand_value
			tier_filters.insert(0, brand_map)

	if location_filter_key and location_value:
		location_map = dict(category_filters)
		location_map[location_filter_key] = location_value
		tier_filters.insert(0, location_map)

	similar_items = similar_items_by_rules(
		base_queryset=base_queryset,
		item=item,
		tier_filters=tier_filters,
		max_items=max_items,
	)

	same_price_queryset = (
		base_queryset
		.exclude(pk=item.pk)
		.filter(**price_filter)
		.order_by("-view_count", "-date_added")[:max_items]
	)

	today_start = timezone.now() - timedelta(days=1)
	popular_today_queryset = (
		base_queryset
		.exclude(pk=item.pk)
		.filter(date_added__gte=today_start)
		.order_by("-view_count", "-date_added")[:max_items]
	)
	if not popular_today_queryset:
		popular_today_queryset = (
			base_queryset
			.exclude(pk=item.pk)
			.order_by("-view_count", "-date_added")[:max_items]
		)

	new_arrivals_queryset = (
		base_queryset
		.exclude(pk=item.pk)
		.order_by("-date_added")[:max_items]
	)

	you_might_like = recommended_items_for_you(
		base_queryset=base_queryset,
		item=item,
		category_filters=category_filters,
		max_items=max_items,
	)

	return {
		"similar": similar_items,
		"same_price": _collect_unique_candidates([same_price_queryset], max_items=max_items),
		"popular_today": _collect_unique_candidates([popular_today_queryset], max_items=max_items),
		"new_arrivals": _collect_unique_candidates([new_arrivals_queryset], max_items=max_items),
		"you_might_like": you_might_like,
	}


def _get_recent_session_map(request):
	return request.session.get(RECENT_SESSION_KEY, {"cars": [], "phones": [], "real_estate": []})


def track_recent_view(request, bucket, object_id):
	recent_map = _get_recent_session_map(request)
	bucket_items = [obj_id for obj_id in recent_map.get(bucket, []) if obj_id != object_id]
	bucket_items.insert(0, object_id)
	recent_map[bucket] = bucket_items[:12]
	request.session[RECENT_SESSION_KEY] = recent_map
	request.session.modified = True


def get_recommended_from_history(request):
	recent_map = _get_recent_session_map(request)
	cars = list(Car.objects.prefetch_related("images").filter(pk__in=recent_map.get("cars", [])[:3]))
	phones = list(Phone.objects.prefetch_related("images").filter(pk__in=recent_map.get("phones", [])[:3]))
	real_estate = list(RealEstate.objects.prefetch_related("images").filter(pk__in=recent_map.get("real_estate", [])[:3]))

	recommendations = []
	for item in cars:
		recommendations.append({"kind": "Voiture", "title": f"{item.brand} {item.model}", "price": item.price, "url": item.get_absolute_url()})
	for item in phones:
		recommendations.append({"kind": "Telephone", "title": f"{item.brand} {item.model}", "price": item.price, "url": item.get_absolute_url()})
	for item in real_estate:
		recommendations.append(
			{
				"kind": "Immobilier",
				"title": f"{item.get_real_estate_type_display()} - {item.location}",
				"price": item.price,
				"url": item.get_absolute_url(),
			}
		)
	return recommendations[:8]


def get_favorite_id_map(user):
	if not user.is_authenticated:
		return {"cars": set(), "phones": set(), "real_estate": set()}

	car_ct = ContentType.objects.get_for_model(Car)
	phone_ct = ContentType.objects.get_for_model(Phone)
	real_estate_ct = ContentType.objects.get_for_model(RealEstate)
	favorites = Favorite.objects.filter(user=user, content_type__in=[car_ct, phone_ct, real_estate_ct])
	result = {"cars": set(), "phones": set(), "real_estate": set()}
	for favorite in favorites:
		if favorite.content_type_id == car_ct.id:
			result["cars"].add(favorite.object_id)
		elif favorite.content_type_id == phone_ct.id:
			result["phones"].add(favorite.object_id)
		elif favorite.content_type_id == real_estate_ct.id:
			result["real_estate"].add(favorite.object_id)
	return result


def get_user_city(request):
	city = (request.GET.get("city") or "").strip()
	if city:
		request.session[USER_CITY_SESSION_KEY] = city
		if request.user.is_authenticated:
			profile, _ = UserMarketplaceProfile.objects.get_or_create(user=request.user)
			if profile.city != city:
				profile.city = city
				profile.save(update_fields=["city", "updated_at"])
		return city

	if request.user.is_authenticated:
		profile, _ = UserMarketplaceProfile.objects.get_or_create(user=request.user)
		if profile.city:
			return profile.city

	return request.session.get(USER_CITY_SESSION_KEY, "")


def _serialize_car_cards(car_queryset, request, favorite_ids=None):
	if favorite_ids is None:
		favorite_ids = get_favorite_id_map(request.user)["cars"]
	items = []
	for index, car in enumerate(car_queryset):
		first_image = car.images.first()
		items.append(
			{
				"id": car.pk,
				"title": f"{car.brand} {car.model}",
				"brand": car.brand,
				"model": car.model,
				"price": str(car.price),
				"year": car.year,
				"mileage": car.mileage,
				"vehicle_type": car.get_vehicle_type_display(),
				"view_count": car.view_count,
				"city": car.city,
				"url": car.get_absolute_url(),
				"image_url": first_image.image.url if first_image and first_image.image else "",
				"badges": build_badges(car, index),
				"is_favorite": car.pk in favorite_ids,
			}
		)
	return items


def _first_image_url(item):
	first_image = item.images.first()
	if first_image and first_image.image:
		return first_image.image.url
	return ""


def _normalize_price_filters(request):
	min_price = request.GET.get("min_price", "").strip()
	max_price = request.GET.get("max_price", "").strip()
	parsed_min = None
	parsed_max = None
	try:
		if min_price:
			parsed_min = Decimal(min_price)
		if max_price:
			parsed_max = Decimal(max_price)
	except Exception:
		parsed_min = None
		parsed_max = None
	return parsed_min, parsed_max


class CarViewSet(viewsets.ModelViewSet):
	serializer_class = CarSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "year", "availability", "vehicle_type", "fuel_type", "transmission", "is_commission"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "year", "mileage", "date_added"]

	def get_queryset(self):
		ensure_seeded_data_safe()
		return Car.objects.prefetch_related("images").all()


class CarImageViewSet(viewsets.ModelViewSet):
	queryset = CarImage.objects.select_related("car").all()
	serializer_class = CarImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class PhoneViewSet(viewsets.ModelViewSet):
	serializer_class = PhoneSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "availability"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "date_added"]

	def get_queryset(self):
		ensure_seeded_data_safe()
		return Phone.objects.prefetch_related("images").all()


class PhoneImageViewSet(viewsets.ModelViewSet):
	queryset = PhoneImage.objects.select_related("phone").all()
	serializer_class = PhoneImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class AccessoryViewSet(viewsets.ModelViewSet):
	serializer_class = AccessorySerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["availability"]
	search_fields = ["name", "description"]
	ordering_fields = ["price", "date_added", "name"]

	def get_queryset(self):
		ensure_seeded_data_safe()
		return Accessory.objects.all()


class RealEstateViewSet(viewsets.ModelViewSet):
	serializer_class = RealEstateSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["real_estate_type", "location", "availability", "is_commission"]
	search_fields = ["location", "description"]
	ordering_fields = ["price", "date_added", "location"]

	def get_queryset(self):
		ensure_seeded_data_safe()
		return RealEstate.objects.prefetch_related("images").all()


class RealEstateImageViewSet(viewsets.ModelViewSet):
	queryset = RealEstateImage.objects.select_related("real_estate").all()
	serializer_class = RealEstateImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class ProposalViewSet(viewsets.ModelViewSet):
	queryset = Proposal.objects.prefetch_related("images").all()
	serializer_class = ProposalSerializer
	permission_classes = [ProposalPermission]


class ProposalImageViewSet(viewsets.ModelViewSet):
	queryset = ProposalImage.objects.select_related("proposal").all()
	serializer_class = ProposalImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class SiteLoginRequiredMixin:
	"""Public storefront mixin kept for compatibility with existing class hierarchy."""


class HomePageView(SiteLoginRequiredMixin, View):
	template_name = "kichefu_store.html"

	def get(self, request):
		ensure_seeded_data_safe()
		cars = Car.objects.prefetch_related("images").all()
		phones = Phone.objects.prefetch_related("images").all()
		accessories = Accessory.objects.all()
		real_estates = RealEstate.objects.prefetch_related("images").all()
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
		}
		return render(request, self.template_name, context)


class SearchSuggestionsView(SiteLoginRequiredMixin, View):
	def get(self, request):
		query = request.GET.get("q", "").strip()
		if len(query) < 2:
			return JsonResponse({"suggestions": []})

		suggestions = []

		cars = Car.objects.filter(Q(brand__icontains=query) | Q(model__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in cars:
			suggestions.append(
				{
					"title": f"{item.brand} {item.model}",
					"category": "Voiture",
					"url": item.get_absolute_url(),
				}
			)

		phones = Phone.objects.filter(Q(brand__icontains=query) | Q(model__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in phones:
			suggestions.append(
				{
					"title": f"{item.brand} {item.model}",
					"category": "Telephone",
					"url": item.get_absolute_url(),
				}
			)

		estates = RealEstate.objects.filter(Q(location__icontains=query) | Q(description__icontains=query)).order_by("-view_count", "-date_added")[:4]
		for item in estates:
			suggestions.append(
				{
					"title": f"{item.get_real_estate_type_display()} {item.location}",
					"category": "Parcelle/Maison",
					"url": item.get_absolute_url(),
				}
			)

		return JsonResponse({"suggestions": suggestions[:10]})


class GlobalSearchView(SiteLoginRequiredMixin, View):
	template_name = "search_results.html"

	def get(self, request):
		query = request.GET.get("q", "").strip()
		category = request.GET.get("category", "all").strip() or "all"
		brand = request.GET.get("brand", "").strip()
		model = request.GET.get("model", "").strip()
		neighborhood = request.GET.get("neighborhood", "").strip()
		min_price, max_price = _normalize_price_filters(request)

		results = []

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

		results.sort(key=lambda result: result["price"])

		paginator = Paginator(results, 18)
		page_obj = paginator.get_page(request.GET.get("page", 1))

		context = {
			"page_obj": page_obj,
			"total_results": len(results),
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


class CarMarketplaceListView(SiteLoginRequiredMixin, View):
	template_name = "cars_marketplace.html"

	def get(self, request):
		ensure_seeded_data_safe()
		user_city = get_user_city(request)
		image_queryset = CarImage.objects.only("id", "car_id", "image", "created_at").order_by("-created_at")
		cars = (
			Car.objects.only(
				"id",
				"brand",
				"model",
				"slug",
				"vehicle_type",
				"year",
				"mileage",
				"fuel_type",
				"transmission",
				"price",
				"city",
				"is_commission",
				"availability",
				"view_count",
				"date_added",
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
				"q": search,
				"brand": brand,
				"vehicle_type": vehicle_type,
				"year": year,
				"max_mileage": max_mileage,
				"fuel_type": fuel_type,
				"transmission": transmission,
				"city": city,
				"min_price": min_price,
				"max_price": max_price,
			},
		}
		return render(request, self.template_name, context)


class CarDetailView(SiteLoginRequiredMixin, View):
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
		contact_phone = car.seller_phone or "+243000000000"
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


class PhoneMarketplaceListView(SiteLoginRequiredMixin, View):
	template_name = "phones_marketplace.html"

	def get(self, request):
		ensure_seeded_data_safe()
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


class PhoneDetailView(SiteLoginRequiredMixin, View):
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


class AccessoryMarketplaceListView(SiteLoginRequiredMixin, View):
	template_name = "accessories_marketplace.html"

	def get(self, request):
		ensure_seeded_data_safe()
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


class RealEstateMarketplaceListView(SiteLoginRequiredMixin, View):
	template_name = "real_estate_marketplace.html"

	def get(self, request):
		ensure_seeded_data_safe()
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


class RealEstateDetailView(SiteLoginRequiredMixin, View):
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


class RegisterView(View):
	template_name = "auth/register.html"

	def _next_url(self, request):
		return request.GET.get("next") or request.POST.get("next") or ""

	def get(self, request):
		if request.user.is_authenticated:
			return redirect("home")
		return render(request, self.template_name, {"form": UserCreationForm(), "next": self._next_url(request)})

	def post(self, request):
		if request.user.is_authenticated:
			return redirect("home")

		form = UserCreationForm(request.POST)
		if not form.is_valid():
			return render(request, self.template_name, {"form": form, "next": self._next_url(request)})

		user = form.save()
		login(request, user)
		next_url = self._next_url(request)
		if next_url:
			return redirect(next_url)
		return redirect("home")


class AgentLoginView(LoginView):
	template_name = "auth/agent_login.html"
	redirect_authenticated_user = True

	def form_valid(self, form):
		if not form.get_user().is_staff:
			form.add_error(None, "Acces reserve aux agents autorises.")
			return self.form_invalid(form)
		return super().form_valid(form)

	def get_success_url(self):
		next_url = self.request.GET.get("next") or self.request.POST.get("next")
		if next_url:
			return next_url
		return reverse("marketplace:agent_dashboard")


class AgentDashboardView(LoginRequiredMixin, View):
	template_name = "agent/dashboard.html"
	login_url = "/agent/connexion/"

	def get(self, request):
		if not request.user.is_staff:
			messages.error(request, "Cet espace est reserve aux agents du site.")
			return redirect("home")

		context = {
			"cars_count": Car.objects.count(),
			"phones_count": Phone.objects.count(),
			"accessories_count": Accessory.objects.count(),
			"real_estate_count": RealEstate.objects.count(),
		}
		return render(request, self.template_name, context)


class ToggleFavoriteView(LoginRequiredMixin, View):
	login_url = "/connexion/"

	def post(self, request, model_name, pk):
		model_map = {"car": Car, "phone": Phone, "real_estate": RealEstate}
		model_class = model_map.get(model_name)
		if model_class is None:
			return redirect("home")

		object_instance = get_object_or_404(model_class, pk=pk)
		content_type = ContentType.objects.get_for_model(model_class)
		favorite, created = Favorite.objects.get_or_create(
			user=request.user,
			content_type=content_type,
			object_id=object_instance.pk,
		)
		if not created:
			favorite.delete()

		next_url = request.POST.get("next", "")
		if next_url:
			return redirect(next_url)
		return redirect("home")


class FavoritesView(LoginRequiredMixin, View):
	login_url = "/connexion/"
	template_name = "favorites.html"

	def get(self, request):
		favorite_map = get_favorite_id_map(request.user)
		cars = Car.objects.prefetch_related("images").filter(pk__in=favorite_map["cars"])
		phones = Phone.objects.prefetch_related("images").filter(pk__in=favorite_map["phones"])
		real_estates = RealEstate.objects.prefetch_related("images").filter(pk__in=favorite_map["real_estate"])
		return render(
			request,
			self.template_name,
			{
				"cars": cars,
				"phones": phones,
				"real_estates": real_estates,
			},
		)


class TogglePriceAlertView(LoginRequiredMixin, View):
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
		except Exception:
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

		next_url = request.POST.get("next") or request.GET.get("next")
		if next_url:
			return redirect(next_url)
		return redirect(instance.get_absolute_url())


class NotificationsView(LoginRequiredMixin, View):
	login_url = "/connexion/"
	template_name = "notifications.html"

	def get(self, request):
		notifications = UserNotification.objects.filter(user=request.user).order_by("-created_at")
		if request.GET.get("mark_read") == "1":
			notifications.filter(is_read=False).update(is_read=True)
		return render(request, self.template_name, {"notifications": notifications[:100]})


class SellWithUsView(SiteLoginRequiredMixin, View):
	template_name = "sell_with_us.html"

	def get(self, request):
		return render(request, self.template_name, {"form": ProposalSellForm()})

	def post(self, request):
		form = ProposalSellForm(request.POST, request.FILES)
		if not form.is_valid():
			return render(request, self.template_name, {"form": form})

		proposal = form.save()
		for image in request.FILES.getlist("photos"):
			ProposalImage.objects.create(proposal=proposal, image=image)

		messages.success(request, "Votre annonce a ete envoyee. Notre equipe vous contacte rapidement.")
		return redirect("marketplace:sell_with_us")


class RobotsTxtView(View):
	def get(self, request):
		lines = [
			"User-agent: *",
			"Allow: /",
			f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
		]
		return HttpResponse("\n".join(lines), content_type="text/plain")


class SitemapXmlView(View):
	def get(self, request):
		urls = [
			request.build_absolute_uri("/"),
			request.build_absolute_uri("/voitures/"),
			request.build_absolute_uri("/telephones/"),
			request.build_absolute_uri("/parcelles/"),
			request.build_absolute_uri("/recherche/"),
		]

		for car in Car.objects.only("slug").all()[:5000]:
			urls.append(request.build_absolute_uri(car.get_absolute_url()))
		for phone in Phone.objects.only("slug").all()[:5000]:
			urls.append(request.build_absolute_uri(phone.get_absolute_url()))
		for listing in RealEstate.objects.only("slug").all()[:5000]:
			urls.append(request.build_absolute_uri(listing.get_absolute_url()))

		body = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
		]
		for link in urls:
			body.append(f"<url><loc>{link}</loc></url>")
		body.append("</urlset>")
		return HttpResponse("".join(body), content_type="application/xml")


class GoogleSiteVerificationView(View):
	pattern = re.compile(r"^google[a-zA-Z0-9]+\.html$")

	def get(self, request, filename):
		if not self.pattern.match(filename):
			return HttpResponse(status=404)
		return HttpResponse(
			f"google-site-verification: {filename}",
			content_type="text/html",
		)
