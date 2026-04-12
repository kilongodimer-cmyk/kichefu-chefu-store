import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from ..models import (
	AvailabilityChoices,
	Car,
	CarImage,
	Favorite,
	Phone,
	PhoneImage,
	RealEstate,
	RealEstateImage,
	RealEstateType,
	Accessory,
	UserMarketplaceProfile,
)


WHATSAPP_DEFAULT = "+243814191316"
LUBUMBASHI_NEIGHBORHOODS = ["Kenya", "Kamalondo", "Katuba", "Ruashi", "Golf", "Bel-Air", "Kalubwe"]
RECENT_SESSION_KEY = "recently_viewed"
USER_CITY_SESSION_KEY = "user_city"
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------

def make_whatsapp_link(phone_number, message):
	"""Construit l'URL wa.me avec numéro formaté et message prérempli."""
	number = (phone_number or WHATSAPP_DEFAULT).replace("+", "").replace(" ", "")
	return f"https://wa.me/{number}?text={quote(message)}"


def build_proposal_whatsapp_message(proposal, image_urls=None):
	"""Assemble un message multi-ligne récapitulant la proposition vendeur."""
	lines = [
		"Bonjour, nouvelle proposition recue depuis le formulaire KICHEFU-CHEFU STORE.",
		f"Nom: {proposal.name}",
		f"Telephone: {proposal.phone_number}",
		f"Type: {proposal.get_asset_type_display()}",
		f"Ville: {proposal.city or '-'}",
		f"Etat: {proposal.get_item_condition_display() if proposal.item_condition else '-'}",
		f"Prix souhaite: {proposal.desired_price} USD",
	]

	if proposal.brand:
		lines.append(f"Marque: {proposal.brand}")
	if proposal.model_name:
		lines.append(f"Modele: {proposal.model_name}")
	if proposal.year:
		lines.append(f"Annee: {proposal.year}")
	if proposal.mileage is not None:
		lines.append(f"Kilometrage: {proposal.mileage} km")
	if proposal.storage:
		lines.append(f"Stockage: {proposal.storage}")
	if proposal.transmission:
		lines.append(f"Transmission: {proposal.get_transmission_display()}")
	if proposal.fuel_type:
		lines.append(f"Carburant: {proposal.get_fuel_type_display()}")
	if proposal.location_details:
		lines.append(f"Localisation: {proposal.location_details}")
	if proposal.surface_area:
		lines.append(f"Surface: {proposal.surface_area}")

	lines.append(f"Description: {proposal.description}")
	if image_urls:
		lines.append("Photos:")
		for index, image_url in enumerate(image_urls, start=1):
			lines.append(f"Photo {index}: {image_url}")
	else:
		lines.append("Photos: envoyees via formulaire (minimum 2).")
	return "\n".join(lines)


# ---------------------------------------------------------------------------
# Proposal → Catalog publisher
# ---------------------------------------------------------------------------

def publish_proposal_to_catalog(proposal):
	"""Convertit une proposition approuvée en annonce publique (car, phone...)."""
	asset_type = proposal.asset_type
	created_object = None

	if asset_type == "car":
		created_object = Car.objects.create(
			brand=proposal.brand,
			model=proposal.model_name,
			vehicle_type=Car.VehicleType.OTHER,
			year=proposal.year,
			mileage=proposal.mileage,
			transmission=proposal.transmission,
			fuel_type=proposal.fuel_type,
			price=proposal.desired_price,
			description=proposal.description,
			seller_phone=proposal.phone_number,
			city=proposal.city or "Lubumbashi",
			is_commission=True,
			availability=AvailabilityChoices.AVAILABLE,
		)
		for proposal_image in proposal.images.all():
			CarImage.objects.create(car=created_object, image=proposal_image.image)

	elif asset_type == "phone":
		created_object = Phone.objects.create(
			brand=proposal.brand,
			model=proposal.model_name,
			storage=proposal.storage,
			price=proposal.desired_price,
			description=proposal.description,
			availability=AvailabilityChoices.AVAILABLE,
		)
		for proposal_image in proposal.images.all():
			PhoneImage.objects.create(phone=created_object, image=proposal_image.image)

	elif asset_type in {"house", "land"}:
		real_estate_type = RealEstateType.HOUSE if asset_type == "house" else RealEstateType.LAND
		created_object = RealEstate.objects.create(
			real_estate_type=real_estate_type,
			location=proposal.location_details or proposal.city or "Lubumbashi",
			price=proposal.desired_price,
			description=proposal.description,
			is_commission=True,
			availability=AvailabilityChoices.AVAILABLE,
		)
		for proposal_image in proposal.images.all():
			RealEstateImage.objects.create(real_estate=created_object, image=proposal_image.image)

	elif asset_type == "accessory":
		created_object = Accessory.objects.create(
			name=proposal.brand or proposal.model_name or "Accessoire",
			price=proposal.desired_price,
			description=proposal.description,
			availability=AvailabilityChoices.AVAILABLE,
		)
		first_image = proposal.images.first()
		if first_image and first_image.image:
			created_object.image = first_image.image
			created_object.save(update_fields=["image"])

	return created_object


# ---------------------------------------------------------------------------
# Badges marketing
# ---------------------------------------------------------------------------

def build_badges(item, index=0):
	"""Calcule les labels marketing visibles sur les cartes produit."""
	badges = []
	if item.date_added >= timezone.now() - timedelta(days=21):
		badges.append("Nouveau")
	if index < 3:
		badges.append("Populaire")
	if getattr(item, "view_count", 0) >= 75:
		badges.append("Best Seller")
	if str(getattr(item, "availability", "")) == "reserved":
		badges.append("Stock limite")
	if str(getattr(item, "availability", "")) == "available" and index % 4 == 0:
		badges.append("Bonne affaire")
	return badges


# ---------------------------------------------------------------------------
# Recommendations engine
# ---------------------------------------------------------------------------

def _price_range(item):
	return item.price * Decimal("0.20")


def _collect_unique_candidates(tier_querysets, max_items=6):
	"""Fusionne des queryset en évitant les doublons et en limitant la taille."""
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
	"""Cherche des annonces proches selon filtres métier et tranche de prix."""
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
	"""Compose un mix d'articles populaires/récents pour alimenter le carrousel."""
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


# ---------------------------------------------------------------------------
# Session / user helpers
# ---------------------------------------------------------------------------

def _get_recent_session_map(request):
	"""Récupère la structure des derniers produits vus stockée en session."""
	return request.session.get(RECENT_SESSION_KEY, {"cars": [], "phones": [], "real_estate": []})


def track_recent_view(request, bucket, object_id):
	"""Empile un identifiant vu récemment pour personnaliser la page d'accueil."""
	recent_map = _get_recent_session_map(request)
	bucket_items = [obj_id for obj_id in recent_map.get(bucket, []) if obj_id != object_id]
	bucket_items.insert(0, object_id)
	recent_map[bucket] = bucket_items[:12]
	request.session[RECENT_SESSION_KEY] = recent_map
	request.session.modified = True


def get_recommended_from_history(request):
	"""Construit une liste courte basée sur l'historique de navigation local."""
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
	"""Retourne les IDs favoris de l'utilisateur par catégorie."""
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
	"""Lit la ville préférée dans la requête ou la session et synchronise le profil si connecté."""
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
	"""Prépare la structure JSON utilisée par l'UI (cards voitures + états favoris)."""
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
	"""Convertit les filtres min/max en Decimal en gérant les valeurs invalides."""
	min_price = request.GET.get("min_price", "").strip()
	max_price = request.GET.get("max_price", "").strip()
	parsed_min = None
	parsed_max = None
	try:
		if min_price:
			parsed_min = Decimal(min_price)
		if max_price:
			parsed_max = Decimal(max_price)
	except (InvalidOperation, ValueError, TypeError):
		parsed_min = None
		parsed_max = None
	return parsed_min, parsed_max
