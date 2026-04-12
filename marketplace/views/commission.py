from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from ..models import Commission, Sale, SellerProfile


class SellerDashboardView(LoginRequiredMixin, View):
	"""Tableau de bord vendeur : mes ventes, commissions dues, historique."""
	template_name = "seller/dashboard.html"
	login_url = "/connexion/"

	def get(self, request):
		try:
			profile = request.user.seller_profile
		except SellerProfile.DoesNotExist:
			return redirect("marketplace:seller_register")

		sales = Sale.objects.filter(seller=profile).select_related("commission")
		commissions = Commission.objects.filter(sale__seller=profile)

		now = timezone.now()
		month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		total_sales = sales.count()
		total_revenue = sales.aggregate(total=Sum("sale_price"))["total"] or Decimal("0.00")
		total_commission_due = commissions.filter(status=Commission.Status.PENDING).aggregate(
			total=Sum("amount")
		)["total"] or Decimal("0.00")
		total_commission_paid = commissions.filter(status=Commission.Status.PAID).aggregate(
			total=Sum("amount")
		)["total"] or Decimal("0.00")

		monthly_sales = sales.filter(created_at__gte=month_start)
		monthly_revenue = monthly_sales.aggregate(total=Sum("sale_price"))["total"] or Decimal("0.00")
		monthly_commission = commissions.filter(
			sale__created_at__gte=month_start
		).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

		recent_sales = sales.order_by("-created_at")[:20]

		context = {
			"seller": profile,
			"total_sales": total_sales,
			"total_revenue": total_revenue,
			"total_commission_due": total_commission_due,
			"total_commission_paid": total_commission_paid,
			"monthly_revenue": monthly_revenue,
			"monthly_commission": monthly_commission,
			"monthly_sales_count": monthly_sales.count(),
			"recent_sales": recent_sales,
		}
		return render(request, self.template_name, context)


class SellerSalesHistoryView(LoginRequiredMixin, View):
	"""Historique complet des ventes d'un vendeur."""
	template_name = "seller/sales_history.html"
	login_url = "/connexion/"

	def get(self, request):
		try:
			profile = request.user.seller_profile
		except SellerProfile.DoesNotExist:
			return redirect("marketplace:seller_register")

		sales = (
			Sale.objects.filter(seller=profile)
			.select_related("commission")
			.order_by("-created_at")
		)

		status_filter = request.GET.get("status", "").strip()
		if status_filter in dict(Commission.Status.choices):
			sales = sales.filter(commission__status=status_filter)

		return render(request, self.template_name, {"sales": sales[:200], "status_filter": status_filter})


class SellerRegisterView(LoginRequiredMixin, View):
	"""Inscription en tant que vendeur (création du SellerProfile)."""
	template_name = "seller/register.html"
	login_url = "/connexion/"

	def get(self, request):
		if hasattr(request.user, "seller_profile"):
			return redirect("marketplace:seller_dashboard")
		return render(request, self.template_name)

	def post(self, request):
		if hasattr(request.user, "seller_profile"):
			return redirect("marketplace:seller_dashboard")

		business_name = request.POST.get("business_name", "").strip()
		phone = request.POST.get("phone", "").strip()
		city = request.POST.get("city", "").strip()
		seller_type = request.POST.get("seller_type", "individual").strip()

		if not phone:
			return render(request, self.template_name, {"error": "Le numero de telephone est obligatoire."})

		if seller_type not in dict(SellerProfile.SellerType.choices):
			seller_type = SellerProfile.SellerType.INDIVIDUAL

		SellerProfile.objects.create(
			user=request.user,
			business_name=business_name,
			phone=phone,
			city=city,
			seller_type=seller_type,
		)
		return redirect("marketplace:seller_dashboard")


# ──────────────────────────────────────────────────────────────
# ADMIN COMMISSION DASHBOARD (staff only)
# ──────────────────────────────────────────────────────────────


class AdminCommissionDashboardView(LoginRequiredMixin, View):
	"""Vue admin : synthese globale des commissions collectees par la plateforme."""
	template_name = "commission/admin_dashboard.html"
	login_url = "/agent/connexion/"

	def get(self, request):
		if not request.user.is_staff:
			return redirect("home")

		now = timezone.now()
		month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		all_commissions = Commission.objects.all()
		all_sales = Sale.objects.all()

		# Totaux globaux
		total_sales_count = all_sales.count()
		total_sales_revenue = all_sales.aggregate(t=Sum("sale_price"))["t"] or Decimal("0.00")
		total_commission_collected = all_commissions.filter(
			status=Commission.Status.PAID
		).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
		total_commission_pending = all_commissions.filter(
			status=Commission.Status.PENDING
		).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

		# Ce mois
		monthly_sales = all_sales.filter(created_at__gte=month_start)
		monthly_revenue = monthly_sales.aggregate(t=Sum("sale_price"))["t"] or Decimal("0.00")
		monthly_commission = all_commissions.filter(
			created_at__gte=month_start
		).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

		# Top vendeurs
		top_sellers = (
			SellerProfile.objects.filter(sales__isnull=False)
			.annotate(
				nb_sales=Count("sales"),
				revenue=Sum("sales__sale_price"),
			)
			.order_by("-revenue")[:10]
		)

		# Dernières commissions
		recent_commissions = (
			all_commissions.select_related("sale", "sale__seller")
			.order_by("-created_at")[:30]
		)

		context = {
			"total_sales_count": total_sales_count,
			"total_sales_revenue": total_sales_revenue,
			"total_commission_collected": total_commission_collected,
			"total_commission_pending": total_commission_pending,
			"monthly_revenue": monthly_revenue,
			"monthly_commission": monthly_commission,
			"monthly_sales_count": monthly_sales.count(),
			"top_sellers": top_sellers,
			"recent_commissions": recent_commissions,
		}
		return render(request, self.template_name, context)
