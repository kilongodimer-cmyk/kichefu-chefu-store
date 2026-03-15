from urllib.parse import quote, urlparse

from django import template

register = template.Library()


@register.filter
def safe_image_url(image_field):
    """Return image URL only if the storage object exists, else empty string."""
    if not image_field:
        return ""

    try:
        name = image_field.name
        storage = image_field.storage
        if not name or storage is None:
            return ""
        original_url = image_field.url
    except Exception:
        return ""

    parsed = urlparse(original_url)
    if parsed.scheme and parsed.netloc:
        try:
            encoded = quote(original_url, safe="")
            return f"https://wsrv.nl/?url={encoded}&output=webp"
        except Exception:
            return original_url

    return original_url


@register.filter
def dummy_webp(url):
    """Ensure dummyimage links also use WebP output."""
    if not url:
        return ""
    return url.replace(".png", ".webp")
