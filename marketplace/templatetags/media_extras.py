from django import template

register = template.Library()


@register.filter
def safe_image_url(image_field):
    """Return the storage URL for an image if it exists, else empty string."""
    if not image_field:
        return ""

    try:
        name = image_field.name
        storage = image_field.storage
        if not name or storage is None:
            return ""
        return image_field.url
    except (AttributeError, OSError, ValueError):
        return ""


@register.filter
def dummy_webp(url):
    """Ensure dummyimage links also use WebP output."""
    if not url:
        return ""
    return url.replace(".png", ".webp")
