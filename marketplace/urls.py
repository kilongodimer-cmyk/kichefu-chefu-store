from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    AccessoryMarketplaceListView,
    AgentDashboardView,
    AgentLoginView,
    CarDetailView,
    CarMarketplaceListView,
    FavoritesView,
    PhoneDetailView,
    PhoneMarketplaceListView,
    RegisterView,
    RealEstateDetailView,
    RealEstateMarketplaceListView,
    SellWithUsView,
    ToggleFavoriteView,
)

app_name = "marketplace"

urlpatterns = [
    path("connexion/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("inscription/", RegisterView.as_view(), name="register"),
    path("deconnexion/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("agent/connexion/", AgentLoginView.as_view(), name="agent_login"),
    path("agent/espace/", AgentDashboardView.as_view(), name="agent_dashboard"),
    path("agent/deconnexion/", auth_views.LogoutView.as_view(next_page="home"), name="agent_logout"),
    path("voitures/", CarMarketplaceListView.as_view(), name="car_list"),
    path("voitures/<int:pk>/", CarDetailView.as_view(), name="car_detail"),
    path("telephones/", PhoneMarketplaceListView.as_view(), name="phone_list"),
    path("telephones/<int:pk>/", PhoneDetailView.as_view(), name="phone_detail"),
    path("accessoires/", AccessoryMarketplaceListView.as_view(), name="accessory_list"),
    path("immobilier/", RealEstateMarketplaceListView.as_view(), name="real_estate_list"),
    path("immobilier/<int:pk>/", RealEstateDetailView.as_view(), name="real_estate_detail"),
    path("vendre-avec-nous/", SellWithUsView.as_view(), name="sell_with_us"),
    path("favoris/", FavoritesView.as_view(), name="favorites"),
    path("favoris/toggle/<str:model_name>/<int:pk>/", ToggleFavoriteView.as_view(), name="toggle_favorite"),
]
