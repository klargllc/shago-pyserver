import os
from django.db import models
from django.contrib.auth.models import User, Permission
from ..utils.helpers import (
	generate_staff_id,
	generate_invoice_id,
	get_average_rating,
	slugify,
	parse_image_url,
)
from rest_framework.authtoken.models import Token
from decimal import Decimal


class Tag(models.Model):
	tag = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.tag


class Category(models.Model):
	name = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name_plural = 'Categories'

	def item_count(self):
		# print(self.restaurant_set)
		return None

	def __str__(self):
		return self.name


class NotificationMessage(models.Model):
	priority = models.CharField(max_length=20)
	message = models.TextField()
	to = models.ForeignKey("Restaurant", on_delete=models.CASCADE)

	class Meta:
		abstract = False


class FoodItem(models.Model):
	name = models.CharField(max_length=150, unique=True)
	customizations = models.ManyToManyField("Customization", blank=True, related_name="customizations")
	about = models.TextField(blank=True, null=True)
	images = models.ManyToManyField("FoodImage", blank=True, related_name="images")
	price = models.DecimalField(decimal_places=2, max_digits=1000)
	category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True, blank=True)
	tags = models.ManyToManyField("Tag", blank=True)
	reviews = models.ManyToManyField("metrics.Review", blank=True, related_name="reviews")
	featured = models.BooleanField(default=False)
	place = models.ForeignKey("Restaurant", on_delete=models.CASCADE)
	slug = models.SlugField(blank=True, null=True)

	# metrics and analytics field
	@property
	def metrics(self):
		from .models import FoodMetric
		_metrics = FoodMetric.objects.filter(item=self)
		return _metrics

	def rating(self):
		reviews = self.reviews.all()
		rate = get_average_rating(reviews)
		return rate

	def __str__(self):
		return self.name

	def image(self):
		imgs = list(self.images.all())
		if len(imgs) > 0:
			return imgs[0]
		return None

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def get_absolute_url(self, *args, **kwargs):
		from django.urls import reverse
		return reverse('admin:detail', {'pk': self.pk})


class FoodImage(models.Model):
	item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
	image = models.ImageField(upload_to='food/')

	def delete(self):
		os.remove(os.path.abspath(self.image.path))
		super().delete()


class Customization(models.Model):
	food_item = models.ForeignKey("FoodItem", on_delete=models.CASCADE)
	title = models.CharField(max_length=150, unique=True)
	options = models.ManyToManyField("CustomizationOption", blank=True, related_name="choices")
	required = models.BooleanField(default=False)
	default_option = models.ForeignKey(
										"CustomizationOption", blank=True,
										null=True, on_delete=models.SET_NULL,
										related_name='default'
										)

	def __str__(self):
		try:
			return self.food_item.name + ' - ' + self.title
		except:
			return self.title


class CustomizationOption(models.Model):
	customization = models.ForeignKey("Customization", related_name='to', on_delete=models.CASCADE)
	option = models.CharField(max_length=100, unique=True)
	price = models.DecimalField(decimal_places=2, max_digits=1000, blank=True)

	def __str__(self):
		return self.option


class Restaurant(models.Model):
	store_mode = models.CharField(max_length=100, default='test') # test | live
	disabled = models.BooleanField(default=False)

	# Basic Info
	name = models.CharField(max_length=200)
	slug = models.SlugField(blank=True, null=True)
	banner = models.ImageField(upload_to="places/banner", blank=True, null=True)
	logo = models.ImageField(upload_to="places/logo", blank=True, null=True)
	about = models.TextField(blank=True, null=True)
	links = models.ManyToManyField("Link", blank=True)
	domian_name = models.CharField(max_length=100, blank=True, null=True)

	owner = models.OneToOneField("accounts.BusinessAccount", on_delete=models.CASCADE)
	staff = models.ManyToManyField("accounts.RestaurantStaff", blank=True, related_name='staff')

	# Menu, Orders and Reviews
	menu = models.ManyToManyField("FoodItem", blank=True)
	categories = models.ManyToManyField("Category", blank=True)
	tags = models.ManyToManyField("Tag", blank=True)
	reviews = models.ManyToManyField("metrics.Review", blank=True)
	orders = models.ManyToManyField("Order", blank=True)
	notifications = models.ManyToManyField("NotificationMessage", blank=True)
	customers = models.ManyToManyField('accounts.Customer', blank=True)

	# Meta Information
	offer_delivery = models.BooleanField(default=False)
	offer_dine_in = models.BooleanField(default=True)
	offer_pickup = models.BooleanField(default=True)

	# Delivery Method
	delivery_fulfilment = models.CharField(max_length=20) # in-house / out-sourced

	currency = models.CharField(max_length=10, blank=True, null=True, default='NGN')
	country = models.CharField(max_length=10, blank=True, null=True, default='NG',)

	# Billing and Payout Info
	billing_plan = models.CharField(max_length=20, default='free-trial')
	next_billing_period = models.DateField(null=True, blank=True)
	current_billing_period = models.DateField(auto_now=True, null=True, blank=True)


	def create(self):
		if not self.slug:
			self.slug = slugify(self.name)
		self.save()
		

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	
	def __str__(self):
		return self.name


class Link(models.Model):
	SERVICES = (
		('custom', 'custom'),
		('facebook', 'facebook'),
		('instagram', 'instagram'),
		('twitter', 'twitter'),
		('whatsapp', 'whatsapp'),
		('telegram', 'telegram'),
		('website', 'website'),
		('tiktok', 'tiktok'),
	)
	place = models.ForeignKey("Restaurant", on_delete=models.CASCADE)
	_type = models.CharField(max_length=40, choices=SERVICES, default='custom')
	url = models.URLField(unique=True)

	def __str__(self):
		return self.url


class Coupon(models.Model):
	COUPON_TYPES = (('Flat', 'flat'), ('Percentage', 'percentage'))

	code = models.CharField(max_length=20, unique=True)
	value = models.DecimalField(max_digits=10, decimal_places=2)
	value_type = models.CharField(max_length=10, default='flat', choices=COUPON_TYPES)
	selector_target = models.CharField(max_length=50, blank=True, default='id') # id|category|tag|price
	selector_value = models.CharField(max_length=100, blank=True, null=True)
	related_place = models.ForeignKey('places.Restaurant', on_delete=models.CASCADE)
	redeemers = models.ManyToManyField('accounts.Customer', blank=True)

	def __str__(self):
		return self.code




