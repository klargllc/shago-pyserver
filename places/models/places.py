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
from accounts.models import DbModel


class Location(DbModel):
	country = models.CharField(max_length=200)
	state = models.CharField(max_length=200)
	city = models.CharField(max_length=200)
	zip_code = models.CharField(max_length=20, blank=True, null=True)
	address = models.CharField(max_length=300, blank=True, null=True)
	meta_info = models.TextField(blank=True, null=True)

	def __str__(self) -> str:
		return self.country

class Tag(DbModel):
	tag = models.CharField(max_length=50, unique=True)

	def __str__(self):
		return self.tag


class Category(DbModel):
	name = models.CharField(max_length=50, unique=True)

	class Meta:
		verbose_name_plural = 'Categories'

	def item_count(self):
		# print(self.restaurant_set)
		return None

	def __str__(self):
		return self.name


class NotificationMessage(DbModel):
	priority = models.CharField(max_length=20)
	message = models.TextField()
	place_id = models.ForeignKey("Restaurant", on_delete=models.CASCADE)
	branch_id = models.ForeignKey("RestaurantBranch", blank=True, null=True, on_delete=models.CASCADE)
	class Meta:
		abstract = False


class FoodItem(DbModel):
	name = models.CharField(max_length=150, unique=True)
	slug = models.SlugField(blank=True, null=True)
	is_package_item = models.BooleanField(default=False)
	includes = models.ManyToManyField('IncludedItem', blank=True)
	custom_choices = models.ManyToManyField("OrderOption", blank=True, related_name="customizations")
	about = models.TextField(blank=True, null=True)
	images = models.ManyToManyField("FoodImage", blank=True, related_name="images")
	price = models.DecimalField(decimal_places=2, max_digits=1000)
	category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True, blank=True)
	tags = models.ManyToManyField("Tag", blank=True)
	reviews = models.ManyToManyField("metrics.Review", blank=True, related_name="reviews")
	featured = models.BooleanField(default=False)
	place = models.ForeignKey("Restaurant", on_delete=models.CASCADE)
	prep_time = models.DurationField(blank=True, null=True)

	# metrics and analytics field
	@property
	def metrics(self):
		pass

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
		if not self.id and not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def get_absolute_url(self, *args, **kwargs):
		from django.urls import reverse
		return reverse('admin:detail', {'pk': self.pk})



class IncludedItem(DbModel):
	name = models.CharField(max_length=200)
	image = models.ImageField(upload_to='food/')


class FoodPackage(FoodItem):
	pass
	# add package items


class FoodImage(DbModel):
	item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
	image = models.ImageField(upload_to='food/')

	def delete(self):
		os.remove(os.path.abspath(self.image.path))
		super().delete()


class OrderOption(DbModel):
	# A customizeable feature on your order
	# for example pizza topping: ['beef', 'pepperonni', 'pineapple']
	food_item = models.ForeignKey("FoodItem", on_delete=models.CASCADE)
	name = models.CharField(max_length=150, unique=True)
	choices = models.ManyToManyField("CustomOptionChoice", blank=True, related_name="choices")
	required = models.BooleanField(default=False)
	default_choice = models.ForeignKey(
		"CustomOptionChoice", blank=True,
		null=True, on_delete=models.SET_NULL,
		related_name='default'
	)

	def __str__(self):
		try:
			return self.food_item.name + ' - ' + self.name
		except:
			return self.title


class CustomOptionChoice(DbModel):
	customization = models.ForeignKey("OrderOption", related_name='to', on_delete=models.CASCADE)
	name = models.CharField(max_length=100, unique=True)
	price = models.DecimalField(decimal_places=2, max_digits=1000, blank=True, null=True)

	def __str__(self):
		return self.name


class Restaurant(DbModel):
	STORE_MODES = (
		('live', 'Live Mode'),
		('test', 'Test Mode'),
	)
	store_mode = models.CharField(max_length=100, default='test', choices=STORE_MODES) # test | live
	disabled = models.BooleanField(default=False)
	offer_delivery = models.BooleanField(default=False)
	offer_dine_in = models.BooleanField(default=False)
	offer_pickup = models.BooleanField(default=False)

	# Basic Info
	name = models.CharField(max_length=200)
	slug = models.SlugField(blank=True, null=True)
	banner = models.ImageField(upload_to="places/banner", blank=True, null=True)
	logo = models.ImageField(upload_to="places/logo", blank=True, null=True)
	about = models.TextField(blank=True, null=True)
	links = models.ManyToManyField("Link", blank=True)
	domian_name = models.CharField(max_length=100, blank=True, null=True)
	owner = models.OneToOneField("accounts.Merchant", on_delete=models.CASCADE)
	staff = models.ManyToManyField("accounts.RestaurantStaff", blank=True, related_name='staff')
	branches = models.ManyToManyField("RestaurantBranch", blank=True, related_name='branches')
	main_branch = models.ForeignKey("RestaurantBranch", blank=True, null=True, on_delete=models.SET_NULL)

	# Menu, Orders and Reviews
	categories = models.ManyToManyField("Category", blank=True)
	menu = models.ManyToManyField('FoodItem', blank=True, related_name='food_items')
	tags = models.ManyToManyField("Tag", blank=True)
	reviews = models.ManyToManyField("metrics.Review", blank=True)
	orders = models.ManyToManyField("Order", blank=True)
	notifications = models.ManyToManyField("NotificationMessage", blank=True)
	customers = models.ManyToManyField('accounts.Customer', blank=True)

	# Delivery Method
	delivery_fulfilment = models.CharField(max_length=20) # in-house / out-sourced

	# Billing and Payout Info
	billing_plan = models.CharField(max_length=20, default='free-trial')
	next_billing_period = models.DateField(null=True, blank=True)
	current_billing_period = models.DateField(auto_now=True, null=True, blank=True)
	billing_information = models.ForeignKey('accounts.BillingMethod', blank=True, null=True, on_delete=models.SET_NULL)
	payout_information = models.ForeignKey('accounts.PayoutInformation', blank=True, null=True, on_delete=models.SET_NULL)

	# Store settings
	# faqs = models.ManyToManyField()
	

	def create(self):
		if not self.slug:
			self.slug = slugify(self.name)
		self.save()
		
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
	
	def place_order(self, order, branch_id):
		self.orders.add((order,))
		_branch:RestaurantBranch = self.branches.get(branch_id=branch_id)
		_branch.related_orders.add((order,))
	
	def __str__(self):
		return self.name



class Currency(DbModel):
	country = models.CharField(max_length=200)
	code = models.CharField(max_length=4)
	symbol = models.CharField(max_length=4)

	class Meta:
		verbose_name_plural = 'Currencies'

	def __str__(self):
		return self.code
	



class RestaurantBranch(DbModel):
	place_id = models.ForeignKey('Restaurant', on_delete=models.CASCADE)
	branch_id = models.CharField(max_length=200, blank=True, default=generate_invoice_id, unique=True)
	branch_name = models.CharField(max_length=200, blank=True, unique=True)
	is_main_branch = models.BooleanField(default=False)
	
	# Meta Information
	offer_delivery = models.BooleanField(default=False)
	offer_dine_in = models.BooleanField(default=True)
	offer_pickup = models.BooleanField(default=True)
	currency = models.ForeignKey('Currency', blank=True, null=True, on_delete=models.SET_NULL)

	location = models.ForeignKey('Location', blank=True, null=True, on_delete=models.SET_NULL)
	inherit_source = models.ForeignKey(blank=True, to='self', on_delete=models.SET_NULL, null=True)
	inherit_menu = models.BooleanField(default=True)
	menu = models.ManyToManyField('FoodItem', blank=True)
	related_orders = models.ManyToManyField('places.Order', blank=True)
	related_staff = models.ManyToManyField('accounts.RestaurantStaff', blank=True)
	is_active = models.BooleanField(blank=True, default=False) # offline/online

	class Meta:
		verbose_name_plural = 'Restaurant Branches'

	def __str__(self) -> str:
		return self.branch_name
	

class Link(DbModel):
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
	place_id = models.ForeignKey("Restaurant", on_delete=models.CASCADE)
	link_type = models.CharField(max_length=40, choices=SERVICES, default='custom')
	link_url = models.URLField(unique=True)

	def __str__(self):
		return self.url


class Coupon(DbModel):
	COUPON_TYPES = (('Flat', 'flat'), ('Percentage', 'percentage'))
	COUPON_SELECTOR = (
		('Id', 'id'),
		('Category', 'category'),
		('Tag', 'tag'),
		('Price', 'price')
	)

	place_id = models.ForeignKey('places.Restaurant', on_delete=models.CASCADE)
	# if branch_ids is present, then coupon will only work in selected stores
	#  like a coupon only available in participating locations
	branch_ids = models.ManyToManyField('places.RestaurantBranch', blank=True)
	redeemers = models.ManyToManyField('accounts.Customer', blank=True)
	name = models.CharField(max_length=200, unique=True, blank=True, null=True)
	code = models.CharField(max_length=20, unique=True, default=generate_invoice_id)
	value = models.DecimalField(max_digits=10, decimal_places=2)
	value_type = models.CharField(max_length=10, default='flat', choices=COUPON_TYPES)
	selector_target = models.CharField(max_length=50, blank=True, default='id') # id|category|tag|price
	selector_value = models.CharField(max_length=100, blank=True, null=True)
	active_from = models.DateTimeField(blank=True, null=True)
	expiry_date = models.DateTimeField(blank=True, null=True)

	def __str__(self):
		return self.code if not self.name else self.name




