import os
from random import randint, choice
from rest_framework.pagination import PageNumberPagination




class ParamObject:
	""" A simple param object inspired by JavaScript URLSearchParams """
	def __init__(self, request):
		self.request = request.GET
		return

	def get(self, key, def_val=None):
		return self.request.get(key, def_val)

	@property
	def param_list(self):
		return self.request.keys()

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		return f'ParamObject: {self.param_list}'

def useParams(req):
	# return a new param object 
	return ParamObject(req)

def get_featured_items(menu):
	featured_items = menu.filter(featured=True)
	featured_items.order_by('?')
	return

def get_cart(person, place):
	from places.models import BuyerCart
	try:
		cart = person.carts.get(restaurant=place)
	except BuyerCart.DoesNotExist:
		cart = BuyerCart.objects.create(owner=person, restaurant=place)
		person.carts.add(cart)
		person.save()
	finally:
		return cart

def paginate_items(items, request, num_per_page=10):
	paginator = PageNumberPagination()
	paginator.page_size = num_per_page
	page_size_query_param = 'page_size'
	paginated_data = paginator.paginate_queryset(items, request)
	data = paginator.get_paginated_response(paginated_data).data
	return data

def add_to_cart(cart, menu_item, qty):
	from places.models import OrderItem
	order_item = OrderItem(item=menu_item, quantity=qty)
	order_item.save()
	cart.items.add(order_item)
	cart.save()
	return order_item


def add_customization(order_item, custom, choice):
	from places.models import OrderCustomization
	custom_option = OrderCustomization(
		customization=custom,
		option=choice
	)
	custom_option.save()
	order_item.customizations.add(custom_option)
	order_item.save()


def generate_staff_id():
	char = os.urandom(4).hex()
	return char


def create_hash(lim=4):
	char = os.urandom(lim).hex()
	return char


def generate_invoice_id():
	char = os.urandom(4).hex()
	return char.upper()


def get_average_rating(reviews):
	_1_stars = 0; _2_stars = 0; _3_stars = 0; _4_stars = 0; _5_stars = 0

	for review in reviews:
		if review.rating == 1:
			_1_stars += 1
		elif review.rating == 2:
			_2_stars += 1
		elif review.rating == 3:
			_3_stars += 1
		elif review.rating == 4:
			_4_stars += 1
		elif review.rating == 5:
			_5_stars += 1

	score = (
		(_1_stars * 1) + 
		(_2_stars * 2) + 
		(_3_stars * 3) + 
		(_4_stars * 4) + 
		(_5_stars * 5)
		)
	
	res = (
		_5_stars +
		_4_stars +
		_3_stars +
		_2_stars +
		_1_stars
		)
	
	if not res == 0:
		ans = round(float(score / res), 1)
		return str(ans)
	return "0.0"


def slugify(string):
	string = string.lower().replace(' ', '-').replace("'", '').replace('.', '')
	return string


