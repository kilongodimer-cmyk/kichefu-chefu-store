import re
import logging
from xml.sax.saxutils import escape as xml_escape

from django.http import HttpResponse
from django.views import View

from ..models import Car, Phone, RealEstate

logger = logging.getLogger(__name__)


class RobotsTxtView(View):
	def get(self, request):
		lines = [
			"User-agent: *",
			"Allow: /",
			f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
		]
		return HttpResponse("\n".join(lines), content_type="text/plain")


class SitemapXmlView(View):
	def get(self, request):
		urls = {
			request.build_absolute_uri("/"),
			request.build_absolute_uri("/voitures/"),
			request.build_absolute_uri("/telephones/"),
			request.build_absolute_uri("/parcelles/"),
			request.build_absolute_uri("/recherche/"),
		}

		querysets = (
			("Car", Car.objects.only("slug").all()[:5000]),
			("Phone", Phone.objects.only("slug").all()[:5000]),
			("RealEstate", RealEstate.objects.only("slug").all()[:5000]),
		)

		for label, queryset in querysets:
			try:
				for item in queryset:
					urls.add(request.build_absolute_uri(item.get_absolute_url()))
			except (AttributeError, TypeError, ValueError):
				logger.exception("Sitemap generation failed for %s", label)

		body = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
		]
		for link in sorted(urls):
			body.append(f"<url><loc>{xml_escape(link)}</loc></url>")
		body.append("</urlset>")
		return HttpResponse("".join(body), content_type="application/xml")


class GoogleSiteVerificationView(View):
	pattern = re.compile(r"^google[a-zA-Z0-9]+\.html$")

	def get(self, request, filename):
		if not self.pattern.match(filename):
			return HttpResponse(status=404)
		return HttpResponse(
			f"google-site-verification: {filename}",
			content_type="text/html",
		)
