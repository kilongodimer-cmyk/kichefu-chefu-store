from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def upload_car_image(instance, filename):
	return f"marketplace/cars/{instance.car_id}/{filename}"


def upload_phone_image(instance, filename):
	return f"marketplace/phones/{instance.phone_id}/{filename}"


def upload_accessory_image(instance, filename):
	return f"marketplace/accessories/{instance.pk}/{filename}"


def upload_real_estate_image(instance, filename):
	return f"marketplace/real_estate/{instance.real_estate_id}/{filename}"


def upload_proposal_image(instance, filename):
	return f"marketplace/proposals/{instance.proposal_id}/{filename}"


class AvailabilityChoices(models.TextChoices):
	AVAILABLE = "available", "Disponible"
	RESERVED = "reserved", "Reserve"
	SOLD = "sold", "Vendu"


class Car(models.Model):
	brand = models.CharField(max_length=60, db_index=True)
	model = models.CharField(max_length=60, db_index=True)
	year = models.PositiveIntegerField(
		validators=[MinValueValidator(1950), MaxValueValidator(timezone.now().year + 1)]
	)
	mileage = models.PositiveIntegerField(validators=[MinValueValidator(0)])
	price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["brand", "model"]),
			models.Index(fields=["availability", "price"]),
			models.Index(fields=["year", "mileage"]),
		]

	def __str__(self):
		return f"{self.brand} {self.model} ({self.year})"


class CarImage(models.Model):
	car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_car_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Car #{self.car_id}"


class Phone(models.Model):
	brand = models.CharField(max_length=60, db_index=True)
	model = models.CharField(max_length=60, db_index=True)
	storage = models.CharField(max_length=40)
	price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["brand", "model"]),
			models.Index(fields=["availability", "price"]),
		]

	def __str__(self):
		return f"{self.brand} {self.model}"


class PhoneImage(models.Model):
	phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_phone_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Phone #{self.phone_id}"


class Accessory(models.Model):
	name = models.CharField(max_length=120)
	price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	image = models.ImageField(upload_to=upload_accessory_image, blank=True, null=True)
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [models.Index(fields=["availability", "price"])]

	def __str__(self):
		return self.name


class RealEstateType(models.TextChoices):
	HOUSE = "house", "Maison"
	LAND = "land", "Parcelle"


class RealEstate(models.Model):
	real_estate_type = models.CharField(max_length=10, choices=RealEstateType.choices)
	location = models.CharField(max_length=140, db_index=True)
	price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["real_estate_type", "location"]),
			models.Index(fields=["availability", "price"]),
		]

	def __str__(self):
		return f"{self.get_real_estate_type_display()} - {self.location}"


class RealEstateImage(models.Model):
	real_estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_real_estate_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image RealEstate #{self.real_estate_id}"


class ProposalAssetType(models.TextChoices):
	CAR = "car", "Voiture"
	HOUSE = "house", "Maison"
	LAND = "land", "Parcelle"


class Proposal(models.Model):
	name = models.CharField(max_length=120)
	phone_number = models.CharField(max_length=30)
	asset_type = models.CharField(max_length=10, choices=ProposalAssetType.choices)
	description = models.TextField(blank=True)
	desired_price = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.name} - {self.get_asset_type_display()}"


class ProposalImage(models.Model):
	proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_proposal_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Proposal #{self.proposal_id}"

# Create your models here.
