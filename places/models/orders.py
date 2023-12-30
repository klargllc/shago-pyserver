from accounts.models import DbModel
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


class OrderItem(DbModel):
	item = models.ForeignKey("places.FoodItem", on_delete=models.CASCADE)
	quantity = models.IntegerField(default=1)
	customizations = models.ManyToManyField("places.OrderCustomization", blank=True)

	def __str__(self):
		return self.item.name

	@property
	def restaurant(self):
		return self.item.place

	@property
	def total(self):
		num = (self.item.price * self.quantity)
		for custom in self.customizations.all():
			num += custom.choice.price
		return Decimal(num)


class BuyerCart(DbModel):
    items = models.ManyToManyField("OrderItem", blank=True)
    restaurant = models.ForeignKey("places.Restaurant", on_delete=models.CASCADE)
    owner = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.owner.name}'s cart @ {self.restaurant.name}"


class OrderCustomization(DbModel):
	customization = models.ForeignKey("places.OrderOption", on_delete=models.CASCADE, blank=True, null=True)
	choice = models.ForeignKey("places.CustomOptionChoice", on_delete=models.CASCADE, blank=True, null=True)

	def __str__(self):
		return self.customization.name


class Order(DbModel): 
	ORDER_STATUS = (
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('ready', 'Ready'),
		('on-route', 'On Route'),
		('delivered', 'Delivered'),
	)
	DELIVERY_OPTIONS = (
		('delivery', 'Delivery'),
		('pickup', 'Pickup'),
	)

	order_id = models.CharField(max_length=12, default=generate_invoice_id, unique=True)
	place_id = models.ForeignKey('places.Restaurant', on_delete=models.CASCADE)
	branch_id = models.ForeignKey('places.RestaurantBranch', on_delete=models.CASCADE)
	customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE)
	source = models.CharField(max_length=20, default='web:shago-meals', blank=True, null=True)
	created_on = models.DateTimeField(blank=True, null=True)
	items = models.ManyToManyField("OrderItem", blank=True)
	pickup_time = models.TimeField(blank=True, null=True)
	delivery_option = models.CharField(max_length=300, default='delivery', choices=DELIVERY_OPTIONS)
	delivery_location = models.ForeignKey("accounts.ShippingAddress", on_delete=models.CASCADE, blank=True, null=True)
	payment_status = models.BooleanField(default=False)
	status = models.CharField(choices=ORDER_STATUS, max_length=20, default='pending')
	payment_id = models.CharField(max_length=10, blank=True, null=True) #flutterwave_txn_ref
	invoice = models.CharField(max_length=30, blank=True, null=True)

	def __str__(self):
		return self.order_id

	def subtotal(self):
		num = 0
		for item in self.items.all():
			num += item.total
		return Decimal(num)
	
	# @property
	# def timesince(self):
	# 	from 


