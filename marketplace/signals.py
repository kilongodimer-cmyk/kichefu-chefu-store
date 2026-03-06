from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Car, Phone, PriceDropAlert, RealEstate, UserMarketplaceProfile, UserNotification


User = get_user_model()


def _ensure_profile(user):
    UserMarketplaceProfile.objects.get_or_create(user=user)


def _notify_new_listing(instance, title, message):
    content_type = ContentType.objects.get_for_model(instance.__class__)
    target_users = UserMarketplaceProfile.objects.filter(notify_new_listings=True).select_related("user")

    notifications = []
    for profile in target_users:
        if isinstance(instance, Car) and profile.city and instance.city:
            if profile.city.strip().lower() != instance.city.strip().lower():
                continue
        notifications.append(
            UserNotification(
                user=profile.user,
                notification_type=UserNotification.NotificationType.NEW_LISTING,
                title=title,
                message=message,
                content_type=content_type,
                object_id=instance.pk,
            )
        )

    if notifications:
        UserNotification.objects.bulk_create(notifications)


def _notify_price_drop(instance, old_price):
    if old_price is None or instance.price >= old_price:
        return

    content_type = ContentType.objects.get_for_model(instance.__class__)
    alerts = PriceDropAlert.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
        is_active=True,
        target_price__gte=instance.price,
    ).select_related("user")

    notifications = []
    for alert in alerts:
        notifications.append(
            UserNotification(
                user=alert.user,
                notification_type=UserNotification.NotificationType.PRICE_DROP,
                title="Baisse de prix detectee",
                message=f"Le produit surveille est passe de {old_price}$ a {instance.price}$.",
                content_type=content_type,
                object_id=instance.pk,
            )
        )
        alert.is_active = False

    if notifications:
        UserNotification.objects.bulk_create(notifications)
        PriceDropAlert.objects.bulk_update(list(alerts), ["is_active"])


@receiver(post_save, sender=User)
def create_marketplace_profile(sender, instance, created, **kwargs):
    if created:
        _ensure_profile(instance)


@receiver(pre_save, sender=Car)
def track_car_previous_price(sender, instance, **kwargs):
    instance._old_price = None
    if instance.pk:
        instance._old_price = Car.objects.filter(pk=instance.pk).values_list("price", flat=True).first()


@receiver(pre_save, sender=Phone)
def track_phone_previous_price(sender, instance, **kwargs):
    instance._old_price = None
    if instance.pk:
        instance._old_price = Phone.objects.filter(pk=instance.pk).values_list("price", flat=True).first()


@receiver(pre_save, sender=RealEstate)
def track_real_estate_previous_price(sender, instance, **kwargs):
    instance._old_price = None
    if instance.pk:
        instance._old_price = RealEstate.objects.filter(pk=instance.pk).values_list("price", flat=True).first()


@receiver(post_save, sender=Car)
def handle_car_events(sender, instance, created, **kwargs):
    if created:
        _notify_new_listing(
            instance=instance,
            title=f"Nouvelle voiture: {instance.brand} {instance.model}",
            message=f"Une nouvelle voiture est disponible a {instance.city or 'votre zone'}.",
        )
    _notify_price_drop(instance, getattr(instance, "_old_price", None))


@receiver(post_save, sender=Phone)
def handle_phone_events(sender, instance, created, **kwargs):
    if created:
        _notify_new_listing(
            instance=instance,
            title=f"Nouveau telephone: {instance.brand} {instance.model}",
            message="Une nouvelle annonce telephone est disponible.",
        )
    _notify_price_drop(instance, getattr(instance, "_old_price", None))


@receiver(post_save, sender=RealEstate)
def handle_real_estate_events(sender, instance, created, **kwargs):
    if created:
        _notify_new_listing(
            instance=instance,
            title=f"Nouvelle annonce immobilier: {instance.location}",
            message="Une nouvelle annonce immobiliere est disponible.",
        )
    _notify_price_drop(instance, getattr(instance, "_old_price", None))
