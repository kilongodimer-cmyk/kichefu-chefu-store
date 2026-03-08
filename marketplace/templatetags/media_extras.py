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
        if not storage.exists(name):
            return ""
        return image_field.url
    except Exception:
        return ""
