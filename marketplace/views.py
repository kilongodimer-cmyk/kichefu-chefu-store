from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .forms import CarSellRequestForm
from .models import (
	Accessory,
	Car,
	CarImage,
	CarSellRequestImage,
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


class CarViewSet(viewsets.ModelViewSet):
	queryset = Car.objects.prefetch_related("images").all()
	serializer_class = CarSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "year", "availability", "vehicle_type", "fuel_type", "transmission"]
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
	filterset_fields = ["real_estate_type", "location", "availability"]
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
		whatsapp_message = f"Bonjour, je suis intéressé par {car.brand} {car.model} sur KICHEFU-CHEFU STORE."
		whatsapp_link = f"https://wa.me/{contact_phone.replace('+', '').replace(' ', '')}?text={whatsapp_message}"

		return render(
			request,
			self.template_name,
			{
				"car": car,
				"contact_phone": contact_phone,
				"whatsapp_link": whatsapp_link,
			},
		)


class SellCarView(View):
	template_name = "sell_car.html"

	def get(self, request):
		return render(request, self.template_name, {"form": CarSellRequestForm()})

	def post(self, request):
		form = CarSellRequestForm(request.POST, request.FILES)
		if not form.is_valid():
			return render(request, self.template_name, {"form": form})

		sell_request = form.save()
		for image in request.FILES.getlist("photos"):
			CarSellRequestImage.objects.create(sell_request=sell_request, image=image)

		messages.success(request, "Votre demande a été envoyée avec succès. Nous vous contacterons rapidement.")
		return redirect("marketplace:sell_car")
