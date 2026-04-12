# Re-export all views for backward-compatible imports:
#   from .views import CarViewSet
#   from marketplace.views import HomePageView

from .api import (  # noqa: F401
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

from .auth import (  # noqa: F401
	AgentLoginView,
	PhoneLoginView,
	RegisterView,
	sanitize_next_url,
)

from .pages import (  # noqa: F401
	AccessoryDetailView,
	AccessoryMarketplaceListView,
	AgentDashboardView,
	CarDetailView,
	CarMarketplaceListView,
	FavoritesView,
	GlobalSearchView,
	HomePageView,
	NotificationsView,
	PhoneDetailView,
	PhoneMarketplaceListView,
	RealEstateDetailView,
	RealEstateMarketplaceListView,
	SearchSuggestionsView,
	SellWithUsView,
	ToggleFavoriteView,
	TogglePriceAlertView,
)

from .seo import (  # noqa: F401
	GoogleSiteVerificationView,
	RobotsTxtView,
	SitemapXmlView,
)
