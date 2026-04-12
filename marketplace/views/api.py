from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from ..models import (
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
from ..permissions import ProposalPermission
from ..serializers import (
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
	"""API REST CRUD complète pour les voitures, filtrable et triable."""
	queryset = Car.objects.prefetch_related("images").all()
	serializer_class = CarSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "year", "availability", "vehicle_type", "fuel_type", "transmission", "is_commission"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "year", "mileage", "date_added"]


class CarImageViewSet(viewsets.ModelViewSet):
	"""Permet d'ajouter ou supprimer les photos rattachées à une voiture."""
	queryset = CarImage.objects.select_related("car").all()
	serializer_class = CarImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class PhoneViewSet(viewsets.ModelViewSet):
	"""Expose la liste des téléphones avec recherche texte et filtres courants."""
	queryset = Phone.objects.prefetch_related("images").all()
	serializer_class = PhoneSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["brand", "model", "availability"]
	search_fields = ["brand", "model", "description"]
	ordering_fields = ["price", "date_added"]


class PhoneImageViewSet(viewsets.ModelViewSet):
	"""Gestion des médias pour les fiches téléphones (upload sécurisé)."""
	queryset = PhoneImage.objects.select_related("phone").all()
	serializer_class = PhoneImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class AccessoryViewSet(viewsets.ModelViewSet):
	"""CRUD API des accessoires (chargeurs, coques, etc.)."""
	queryset = Accessory.objects.all()
	serializer_class = AccessorySerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["availability"]
	search_fields = ["name", "description"]
	ordering_fields = ["price", "date_added", "name"]


class RealEstateViewSet(viewsets.ModelViewSet):
	"""Expose les biens immobiliers avec possibilités de filtrer par type/quartier."""
	queryset = RealEstate.objects.prefetch_related("images").all()
	serializer_class = RealEstateSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ["real_estate_type", "location", "availability", "is_commission"]
	search_fields = ["location", "description"]
	ordering_fields = ["price", "date_added", "location"]


class RealEstateImageViewSet(viewsets.ModelViewSet):
	"""Upload et suppression des visuels pour chaque bien immobilier."""
	queryset = RealEstateImage.objects.select_related("real_estate").all()
	serializer_class = RealEstateImageSerializer
	permission_classes = [permissions.IsAuthenticated]


class ProposalViewSet(viewsets.ModelViewSet):
	"""Back-office REST pour suivre les propositions entrantes et leurs statuts."""
	queryset = Proposal.objects.prefetch_related("images").all()
	serializer_class = ProposalSerializer
	permission_classes = [ProposalPermission]


class ProposalImageViewSet(viewsets.ModelViewSet):
	"""Expose les pièces jointes envoyées par les vendeurs."""
	queryset = ProposalImage.objects.select_related("proposal").all()
	serializer_class = ProposalImageSerializer
	permission_classes = [permissions.IsAuthenticated]
