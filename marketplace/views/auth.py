from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from ..forms import PhoneAuthenticationForm, PhoneSignupForm
from ..models import Accessory, Car, Phone, RealEstate


def sanitize_next_url(request, candidate):
	"""Valide un URL de redirection pour éviter les open-redirect."""
	candidate = (candidate or "").strip()
	if not candidate:
		return ""
	if url_has_allowed_host_and_scheme(candidate, {request.get_host()}, require_https=request.is_secure()):
		return candidate
	return ""


class PhoneLoginView(LoginView):
	template_name = "auth/login.html"
	form_class = PhoneAuthenticationForm
	redirect_authenticated_user = True

	def get_success_url(self):
		next_url = sanitize_next_url(self.request, self.request.POST.get("next") or self.request.GET.get("next"))
		return next_url or reverse("home")


class RegisterView(View):
	template_name = "auth/register.html"

	def _next_url(self, request):
		candidate = request.GET.get("next") or request.POST.get("next") or ""
		return sanitize_next_url(request, candidate)

	def get(self, request):
		if request.user.is_authenticated:
			return redirect("home")
		return render(request, self.template_name, {"form": PhoneSignupForm(), "next": self._next_url(request)})

	def post(self, request):
		if request.user.is_authenticated:
			return redirect("home")

		form = PhoneSignupForm(request.POST)
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
		next_url = sanitize_next_url(self.request, self.request.GET.get("next") or self.request.POST.get("next"))
		if next_url:
			return next_url
		return reverse("marketplace:agent_dashboard")
