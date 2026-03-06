from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from urllib.parse import quote
from datetime import timedelta

from .forms import ProposalSellForm
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


def make_whatsapp_link(phone_number, message):
	number = (phone_number or WHATSAPP_DEFAULT).replace("+", "").replace(" ", "")
	return f"https://wa.me/{number}?text={quote(message)}"


def build_badges(item, index=0):
	badges = []
	if item.date_added >= timezone.now() - timedelta(days=21):
		badges.append("Nouveau")
	if index < 3:
		badges.append("Populaire")
	if str(getattr(item, "availability", "")) == "available" and index % 4 == 0:
		badges.append("Bonne affaire")
	return badges


class CarViewSet(viewsets.ModelViewSet):
	queryset = Car.objects.prefetch_related("images").all()
	serializer_class = CarSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "year", "availability", "vehicle_type", "fuel_type", "transmission", "is_commission"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "year", "mileage", "date_added"]


class CarImageViewSet(viewsets.ModelViewSet):
	queryset = CarImage.objects.select_related("car").all()
	serializer_class = CarImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class PhoneViewSet(viewsets.ModelViewSet):
	queryset = Phone.objects.prefetch_related("images").all()
	serializer_class = PhoneSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "availability"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "date_added"]


class PhoneImageViewSet(viewsets.ModelViewSet):
	queryset = PhoneImage.objects.select_related("phone").all()
	serializer_class = PhoneImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class AccessoryViewSet(viewsets.ModelViewSet):
	queryset = Accessory.objects.all()
	serializer_class = AccessorySerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["availability"]
	search_fields = ["name", "description"]
	ordering_fields = ["price", "date_added", "name"]


class RealEstateViewSet(viewsets.ModelViewSet):
	queryset = RealEstate.objects.prefetch_related("images").all()
	serializer_class = RealEstateSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["real_estate_type", "location", "availability", "is_commission"]
	search_fields = ["location", "description"]
	ordering_fields = ["price", "date_added", "location"]


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
		cars = Car.objects.prefetch_related("images").all()
		phones = Phone.objects.prefetch_related("images").all()
		accessories = Accessory.objects.all()
		real_estates = RealEstate.objects.prefetch_related("images").all()

		popular_cars = list(cars.filter(availability="available")[:6])
		new_cars = list(cars.filter(date_added__gte=timezone.now() - timedelta(days=30))[:6])
		popular_phones = list(phones.filter(availability="available")[:6])
		recent_real_estates = list(real_estates.filter(location__in=LUBUMBASHI_NEIGHBORHOODS)[:6])

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

		context = {
			"popular_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(popular_cars)],
			"new_cars": [(item, build_badges(item, idx)) for idx, item in enumerate(new_cars)],
			"popular_phones": [(item, build_badges(item, idx)) for idx, item in enumerate(popular_phones)],
			"top_accessories": [(item, build_badges(item, idx)) for idx, item in enumerate(accessories.filter(availability="available")[:6])],
			"recent_real_estates": [(item, build_badges(item, idx)) for idx, item in enumerate(recent_real_estates)],
			"best_offers": best_offers,
			"lubumbashi_areas": LUBUMBASHI_NEIGHBORHOODS,
		}
		return render(request, self.template_name, context)


class CarMarketplaceListView(View):
	template_name = "cars_marketplace.html"

	def get(self, request):
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
		contact_phone = car.seller_phone or "+243000000000"
		whatsapp_message = f"Bonjour, je suis interesse par {car.brand} {car.model} sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(contact_phone, whatsapp_message)
		similar_cars = Car.objects.prefetch_related("images").filter(brand=car.brand).exclude(pk=car.pk)[:6]
		recommended_cars = Car.objects.prefetch_related("images").filter(vehicle_type=car.vehicle_type).exclude(pk=car.pk)[:6]

		return render(
			request,
			self.template_name,
			{
				"car": car,
				"contact_phone": contact_phone,
				"whatsapp_link": whatsapp_link,
				"similar_cars": similar_cars,
				"recommended_cars": recommended_cars,
			},
		)


class PhoneMarketplaceListView(View):
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
			"brands": Phone.objects.values_list("brand", flat=True).distinct().order_by("brand"),
			"filters": {"q": search, "brand": brand, "min_price": min_price, "max_price": max_price},
		}
		return render(request, self.template_name, context)


class PhoneDetailView(View):
	template_name = "phone_detail.html"

	def get(self, request, pk):
		phone = get_object_or_404(Phone.objects.prefetch_related("images"), pk=pk)
		whatsapp_message = f"Bonjour, je veux le {phone.brand} {phone.model} vu sur KICHEFU-CHEFU STORE."
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		similar_phones = Phone.objects.prefetch_related("images").filter(brand=phone.brand).exclude(pk=phone.pk)[:6]
		recommended_phones = Phone.objects.prefetch_related("images").filter(storage=phone.storage).exclude(pk=phone.pk)[:6]
		return render(
			request,
			self.template_name,
			{
				"phone": phone,
				"whatsapp_link": whatsapp_link,
				"similar_phones": similar_phones,
				"recommended_phones": recommended_phones,
			},
		)


class AccessoryMarketplaceListView(View):
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


class RealEstateMarketplaceListView(View):
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
			"estate_types": RealEstate._meta.get_field("real_estate_type").choices,
			"lubumbashi_areas": LUBUMBASHI_NEIGHBORHOODS,
			"filters": {"real_estate_type": estate_type, "location": location, "q": search},
		}
		return render(request, self.template_name, context)


class RealEstateDetailView(View):
	template_name = "real_estate_detail.html"

	def get(self, request, pk):
		listing = get_object_or_404(RealEstate.objects.prefetch_related("images"), pk=pk)
		whatsapp_message = (
			f"Bonjour, je suis interesse par cette annonce {listing.get_real_estate_type_display()} a {listing.location}."
		)
		whatsapp_link = make_whatsapp_link(WHATSAPP_DEFAULT, whatsapp_message)
		similar_listings = RealEstate.objects.prefetch_related("images").filter(
			real_estate_type=listing.real_estate_type,
			location=listing.location,
		).exclude(pk=listing.pk)[:6]
		recommended_listings = RealEstate.objects.prefetch_related("images").filter(
			real_estate_type=listing.real_estate_type
		).exclude(pk=listing.pk)[:6]
		return render(
			request,
			self.template_name,
			{
				"listing": listing,
				"whatsapp_link": whatsapp_link,
				"similar_listings": similar_listings,
				"recommended_listings": recommended_listings,
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
