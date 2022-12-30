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


class OrderItem(models.Model):
	item = models.ForeignKey("places.FoodItem", on_delete=models.CASCADE)
	quantity = models.IntegerField(default=1)
	customizations = models.ManyToManyField("places.OrderCustomization", blank=True)

	def __str__(self):
		return self.item.title

	@property
	def restaurant(self):
		return self.item.place

	@property
	def total(self):
		num = (self.item.price * self.quantity)
		for custom in self.customizations.all():
			num += custom.option.price
		return Decimal(num)


class OrderCustomization(models.Model):
	customization = models.ForeignKey("places.Customization", on_delete=models.CASCADE)
	option = models.ForeignKey("places.CustomizationOption", on_delete=models.CASCADE)

	def __str__(self):
		return self.customization.title


class Order(models.Model): 
	ORDER_STATUS = (
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('ready', 'Ready'),
		('on-route', 'On Route'),
		('delivered', 'Delivered'),
	)
	ORDER_SOURCES = (
		("hotspot", "hotspot"),
		("offline", "offline"),
		("website", "hotspot"),
	)
	source = models.CharField(max_length=20, default='hotspot:admin:web', blank=True, null=True)
	customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE)
	created_on = models.DateTimeField(auto_now=True)
	items = models.ManyToManyField("OrderItem", blank=True)
	paid = models.BooleanField(default=False)
	delivered = models.BooleanField(default=False) # delivery_status
	status = models.CharField(choices=ORDER_STATUS, max_length=20, default='pending')
	delivery_is_on = models.BooleanField(default=False)
	invoice = models.CharField(max_length=12, default=generate_invoice_id, unique=True)

	def __str__(self):
		return self.invoice_id

	def subtotal(self):
		num = 0
		for item in self.items.all():
			num += item.total
		return Decimal(num)


