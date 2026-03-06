from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import F, Q
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
	Phone,
	PhoneImage,
	Proposal,
	ProposalImage,
	RealEstate,
	RealEstateImage,
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


def similar_by_price(queryset, item, limit=6):
	price_delta = _price_range(item)
	return queryset.filter(price__gte=item.price - price_delta, price__lte=item.price + price_delta).exclude(pk=item.pk)[:limit]


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
		recommendations.append({"kind": "Voiture", "title": f"{item.brand} {item.model}", "price": item.price, "url": f"/voitures/{item.pk}/"})
	for item in phones:
		recommendations.append({"kind": "Telephone", "title": f"{item.brand} {item.model}", "price": item.price, "url": f"/telephones/{item.pk}/"})
	for item in real_estate:
		recommendations.append(
			{
				"kind": "Immobilier",
				"title": f"{item.get_real_estate_type_display()} - {item.location}",
				"price": item.price,
				"url": f"/immobilier/{item.pk}/",
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


class HomePageView(View):
	template_name = "kichefu_store.html"

	def get(self, request):
		ensure_seeded_data_safe()
		cars = Car.objects.prefetch_related("images").all()
		phones = Phone.objects.prefetch_related("images").all()
		accessories = Accessory.objects.all()
		real_estates = RealEstate.objects.prefetch_related("images").all()

		popular_cars = list(cars.filter(availability="available")[:6])
		new_cars = list(cars.filter(date_added__gte=timezone.now() - timedelta(days=30))[:6])
		popular_phones = list(phones.filter(availability="available")[:6])
		recent_real_estates = list(real_estates.filter(location__in=LUBUMBASHI_NEIGHBORHOODS)[:6])
		hot_cars = list(cars.order_by("-view_count", "-date_added")[:6])
		hot_phones = list(phones.order_by("-view_count", "-date_added")[:6])
		hot_real_estate = list(real_estates.order_by("-view_count", "-date_added")[:6])

		best_offers = []
		for car in cars.filter(availability="available").order_by("price")[:4]:
			best_offers.append({"kind": "Voiture", "title": f"{car.brand} {car.model}", "price": car.price, "url": f"/voitures/{car.pk}/"})
		for phone in phones.filter(availability="available").order_by("price")[:4]:
			best_offers.append({"kind": "Telephone", "title": f"{phone.brand} {phone.model}", "price": phone.price, "url": f"/telephones/{phone.pk}/"})
		for listing in real_estates.filter(availability="available").order_by("price")[:4]:
			best_offers.append(
				{
					"kind": "Immobilier",
					"title": f"{listing.get_real_estate_type_display()} a {listing.location}",
					"price": listing.price,
					"url": f"/immobilier/{listing.pk}/",
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
			"favorite_car_ids": favorite_map["cars"],
			"favorite_phone_ids": favorite_map["phones"],
			"favorite_real_estate_ids": favorite_map["real_estate"],
			"lubumbashi_areas": LUBUMBASHI_NEIGHBORHOODS,
		}
		return render(request, self.template_name, context)


class CarMarketplaceListView(View):
	template_name = "cars_marketplace.html"

	def get(self, request):
		ensure_seeded_data_safe()
		cars = Car.objects.prefetch_related("images").all()

		search = request.GET.get("q", "").strip()
		brand = request.GET.get("brand", "").strip()
		vehicle_type = request.GET.get("vehicle_type", "").strip()
		year = request.GET.get("year", "").strip()
		max_mileage = request.GET.get("max_mileage", "").strip()
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

		try:
			if min_price:
				cars = cars.filter(price__gte=float(min_price))
			if max_price:
				cars = cars.filter(price__lte=float(max_price))
		except ValueError:
			pass

		paginator = Paginator(cars, 12)
		page_obj = paginator.get_page(request.GET.get("page", 1))

		context = {
			"page_obj": page_obj,
			"brands": Car.objects.values_list("brand", flat=True).distinct().order_by("brand"),
			"vehicle_types": Car.VehicleType.choices,
			"car_items": [(item, build_badges(item, idx)) for idx, item in enumerate(page_obj.object_list)],
			"favorite_car_ids": get_favorite_id_map(request.user)["cars"],
			"filters": {
				"q": search,
				"brand": brand,
				"vehicle_type": vehicle_type,
				"year": year,
				"max_mileage": max_mileage,
				"min_price": min_price,
				"max_price": max_price,
			},
		}
		return render(request, self.template_name, context)


class CarDetailView(View):
	template_name = "car_detail.html"

	def get(self, request, pk):
		car = get_object_or_404(Car.objects.prefetch_related("images"), pk=pk)
		Car.objects.filter(pk=car.pk).update(view_count=F("view_count") + 1)
		car.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "cars", car.pk)
		favorite_map = get_favorite_id_map(request.user)
		contact_phone = car.seller_phone or "+243000000000"
		whatsapp_message = f"Bonjour, je suis interesse par {car.brand} {car.model} sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(contact_phone, whatsapp_message)
		similar_cars = similar_by_price(
			Car.objects.prefetch_related("images").filter(brand=car.brand, vehicle_type=car.vehicle_type), car
		)
		recommended_cars = Car.objects.prefetch_related("images").filter(vehicle_type=car.vehicle_type).exclude(pk=car.pk)[:6]

		return render(
			request,
			self.template_name,
			{
				"car": car,
				"contact_phone": contact_phone,
				"whatsapp_link": whatsapp_link,
				"is_favorite": car.pk in favorite_map["cars"],
				"similar_cars": similar_cars,
				"recommended_cars": recommended_cars,
			},
		)


class PhoneMarketplaceListView(View):
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


class PhoneDetailView(View):
	template_name = "phone_detail.html"

	def get(self, request, pk):
		phone = get_object_or_404(Phone.objects.prefetch_related("images"), pk=pk)
		Phone.objects.filter(pk=phone.pk).update(view_count=F("view_count") + 1)
		phone.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "phones", phone.pk)
		favorite_map = get_favorite_id_map(request.user)
		whatsapp_message = f"Bonjour, je veux le {phone.brand} {phone.model} vu sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		similar_phones = similar_by_price(Phone.objects.prefetch_related("images").filter(brand=phone.brand), phone)
		recommended_phones = Phone.objects.prefetch_related("images").filter(storage=phone.storage).exclude(pk=phone.pk)[:6]
		return render(
			request,
			self.template_name,
			{
				"phone": phone,
				"whatsapp_link": whatsapp_link,
				"is_favorite": phone.pk in favorite_map["phones"],
				"similar_phones": similar_phones,
				"recommended_phones": recommended_phones,
			},
		)


class AccessoryMarketplaceListView(View):
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


class RealEstateMarketplaceListView(View):
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


class RealEstateDetailView(View):
	template_name = "real_estate_detail.html"

	def get(self, request, pk):
		listing = get_object_or_404(RealEstate.objects.prefetch_related("images"), pk=pk)
		RealEstate.objects.filter(pk=listing.pk).update(view_count=F("view_count") + 1)
		listing.refresh_from_db(fields=["view_count"])
		track_recent_view(request, "real_estate", listing.pk)
		favorite_map = get_favorite_id_map(request.user)
		whatsapp_message = (
			f"Bonjour, je suis interesse par cette annonce {listing.get_real_estate_type_display()} a {listing.location}."
		)
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		similar_listings = similar_by_price(RealEstate.objects.prefetch_related("images").filter(
			real_estate_type=listing.real_estate_type,
			location=listing.location,
		), listing)
		recommended_listings = RealEstate.objects.prefetch_related("images").filter(
			real_estate_type=listing.real_estate_type
		).exclude(pk=listing.pk)[:6]
		return render(
			request,
			self.template_name,
			{
				"listing": listing,
				"whatsapp_link": whatsapp_link,
				"is_favorite": listing.pk in favorite_map["real_estate"],
				"similar_listings": similar_listings,
				"recommended_listings": recommended_listings,
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


class SellWithUsView(View):
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
