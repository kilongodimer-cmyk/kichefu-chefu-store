from django.urls import path

from .views import CarDetailView, CarMarketplaceListView, SellCarView

app_name = "marketplace"

urlpatterns = [
    path("", CarMarketplaceListView.as_view(), name="car_list"),
    path("vendre/", SellCarView.as_view(), name="sell_car"),
    path("<int:pk>/", CarDetailView.as_view(), name="car_detail"),
]
