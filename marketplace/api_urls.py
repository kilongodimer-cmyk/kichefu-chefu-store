from rest_framework.routers import DefaultRouter

from .views import (
    AccessoryViewSet,
    CarImageViewSet,
    CarViewSet,
    PhoneImageViewSet,
    PhoneViewSet,
    ProposalImageViewSet,
    ProposalViewSet,
    RealEstateImageViewSet,
    RealEstateViewSet,
)

router = DefaultRouter()
router.register(r"cars", CarViewSet, basename="car")
router.register(r"car-images", CarImageViewSet, basename="car-image")
router.register(r"phones", PhoneViewSet, basename="phone")
router.register(r"phone-images", PhoneImageViewSet, basename="phone-image")
router.register(r"accessories", AccessoryViewSet, basename="accessory")
router.register(r"real-estate", RealEstateViewSet, basename="real-estate")
router.register(r"real-estate-images", RealEstateImageViewSet, basename="real-estate-image")
router.register(r"proposals", ProposalViewSet, basename="proposal")
router.register(r"proposal-images", ProposalImageViewSet, basename="proposal-image")

urlpatterns = router.urls
