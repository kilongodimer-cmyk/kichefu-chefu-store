from django.urls import path

from .views import (
    AccessoryMarketplaceListView,
    CarDetailView,
    CarMarketplaceListView,
    PhoneDetailView,
    PhoneMarketplaceListView,
    RealEstateDetailView,
    RealEstateMarketplaceListView,
    SellWithUsView,
)

app_name = "marketplace"

urlpatterns = [
    path("voitures/", CarMarketplaceListView.as_view(), name="car_list"),
    path("voitures/<int:pk>/", CarDetailView.as_view(), name="car_detail"),
    path("telephones/", PhoneMarketplaceListView.as_view(), name="phone_list"),
    path("telephones/<int:pk>/", PhoneDetailView.as_view(), name="phone_detail"),
    path("accessoires/", AccessoryMarketplaceListView.as_view(), name="accessory_list"),
    path("immobilier/", RealEstateMarketplaceListView.as_view(), name="real_estate_list"),
    path("immobilier/<int:pk>/", RealEstateDetailView.as_view(), name="real_estate_detail"),
    path("vendre-avec-nous/", SellWithUsView.as_view(), name="sell_with_us"),
]
