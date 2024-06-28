import os, json
from utils import *
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from rest_framework.response import Response
from .serializers import (
	FoodSerializer,
	CustomerSerializer,
	OrderSerializer,
	UserSerializer,
	ReviewSerializer,
	OrderItemSerializer,
	NotificationSerializer,
	CategorySerializer,
	TagSerializer,
	RestaurantSerializer,
	CartSerializer,
)
from django.contrib.auth import login, logout
from ..models import *
from accounts.models import (
	Customer,
	Account,
)
from metrics.models import (
	Review
)
from rest_framework.decorators import api_view
from dashboard.views import required_params


#  Helpers

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


def get_related_items(place, food):
	items = place.menu.filter(
		Q(name__icontains=food.name)|
		Q(category__name__iexact=food.category.name)
	).exclude(name__iexact=food.name, id__iexact=food.id)
	return items


def get_featured_items():
	featured_items = FoodItem.objects.filter(featured=True)
	featured_items.order_by('?')
	return


def get_cart(person, place):
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
	order_item = OrderItem(item=menu_item, quantity=qty)
	order_item.save()
	cart.items.add(order_item)
	cart.save()
	return order_item


def add_customization(order_item, custom, choice):
	custom_option = OrderCustomization(
		customization=custom,
		option=choice
		)
	custom_option.save()
	order_item.customizations.add(custom_option)
	order_item.save()


# =========== Auth Views ==================

@api_view(["POST"])
def signup_view(request):
	try:
		user_account = Account(
			email=request.data['email'],
			first_name=request.data['first_name'],
			last_name=request.data['last_name'],
		)
		user_account.set_password(request.data['password'])
		user_account.save()

		token = Token.objects.create(user=user_account)
		customer_profile = Customer(
			user=user_account,
			phone=request.data['phone']
		)
		customer_profile.save()

		data = {
			'profile': {
				'user': UserSerializer(user_account).data,
				'token': token.key
			},
			'error': False,
			'message': "Successfully created your account"
		}
		return Response(data)
	except Exception as e:
		return Response({'error': True, 'message': str(e)})


@api_view(["POST"])
def login_view(request):
	try:
		user = Account.objects.get(email=request.data['email'])
		if user.check_password(request.data['password']):
			person = Customer.objects.get(user=user)
			login(request, user)
			data = {
				'user': CustomerSerializer(person).data,
				'token': Token.objects.get_or_create(user=user)[0].key
			}
			return Response(data)
		else:
			return Response(data={'error': True, 'message': 'Invalid login credentials!'}, status=404)
	except Exception:
		raise Exception
		return Response(data={'error': True, 'message': 'Invalid login credentials!'}, status=404)

# =========================================


# ========== Restaurant View ==============

@api_view(["GET"])
def search_view(request):
	query = useParams(request).get('query', None)
	_filter = useParams(request).get('filter', None)

	if query:
		items = FoodItem.objects.filter(title__icontains=query)
		if _filter:
			items = items.filter(category__name__iexact=_filter)
		paginator = PageNumberPagination()
		paginator.page_size = 20
		page = dict(paginator.get_paginated_response(
				paginator.paginate_queryset(items, request)
			).data)
		results = FoodSerializer(page['results'], many=True).data
		res = {
			'error': None,
			"results": results,
			'next': page['next'],
			'previous': page['previous'],
		}
	else:
		res = {
			'error': True,
			'error_text': "Search param is missing"
		}
	return Response(res)



# @required_params('place')
@api_view(['GET'])
def place_view(request):
	place = request.place
	data = RestaurantSerializer(place, context={'request': request}).data
	return Response(data)


# @required_params('place')
@api_view(["GET"])
def menu_view(request):
	params = useParams(request)
	org  = params.get('place')
	category = params.get('cat')
	place = Restaurant.objects.get(slug=org)
	menu = place.menu.all()

	if category:
		menu = menu.filter(category__name__iexact=category)

	featured_items = get_featured_items()
	results = paginate_items(menu, request)

	if request.user.is_authenticated:
		user = request.user
		customer_profile = Customer.objects.get_or_create(user=user)[0]

	try:
		page = dict(results)
		data = {
			'error': False,
			'data': {
				'products': FoodSerializer(page['results'], many=True, context={'request': request}).data,
				'categories': CategorySerializer(place.categories.all(), many=True).data,
				'featured_items': FoodSerializer(featured_items, many=True, context={'request': request}).data
			},
			'next_url': page['next'],
			'previous_url': page['previous'],
			'count': page['count'],
		}
		return Response(data=data, status=200)
	except Exception as e:
		return Response(data={'error': True, 'message': str(e)}, status=500)


# @required_params('place', 'itemId')
@api_view(["GET"])
def item_detail_view(request, **kwargs):
	try:
		params = useParams(request)
		place = Restaurant.objects.get(slug=params.get('place'))
		foodId = params.get('itemId')
		food_item = place.menu.get(slug=foodId)
		related_items = get_related_items(place, food_item)

		data = {
			'item': FoodSerializer(food_item, context={'request': request}).data,
			'related_items': FoodSerializer(related_items, context={'request': request}, many=True).data,
			'error': False,
		}

		return Response(status=200, data=data)
	except Exception as e:
		# print("Error:", e) # log instead
		return Response(status=500, data={'error': True, 'message': str(e)})



# @required_params('place')
@api_view(["GET", "POST"])
def cart_view(request):
	customer = Customer.objects.get(user=request.user)
	params = useParams(request)
	place = Restaurant.objects.get(slug=params.get('place'))
	cart = get_cart(customer, place)

	#  customization format
	# {
	#	...
	# 	'customizations': {
	# 		'dressing' : {'option' : 'coleslaw'},
	# 		'meat' : {'option' : 'turkey'}
	# 	}
	# }

	try:
		if request.method == "POST":
			if request.data['action'] == 'add-to-cart':
				food_item = place.menu.get(slug=request.data['item'])
				order_item = add_to_cart(cart, food_item, request.data.get('qty', 1))				

				if request.data.get('customizations', None):
					customizations = request.data['customizations']

					for key in customizations.keys():
						custom = food_item.customizations.get(title=key)
						choice = customizations[key]['option']
						option = custom.options.get(option=choice)
						add_customization(order_item, custom, option)
						
					cart.items.add(order_item)
					cart.save()
					return Response({'error': None, 'message': 'Successfully added item to cart'})

			elif request.data['action'] == 'remove-from-cart':
				print(request.data)
				order_item = cart.items.get(id=request.data['item'])
				order_item.delete()
				return Response({'error': None, 'message': 'Successfully removed item from cart'})

			elif request.data['action'] == 'decrease-order':
				order_item = cart.items.get(id=request.data['item'])
				order_item.quantity -= 1
				order_item.save()

			elif request.data['action'] == 'increase-order':
				order_item = cart.items.get(id=request.data['item'])
				order_item.quantity += 1
				order_item.save()

		data = {
			'error': False,
			"cart": CartSerializer(cart, context={'request': request}).data
		}
		return Response(data=data)
	except Exception as e:
		raise e
		return Response(data={'error': True, 'message': str(e)}, status=500)


# @required_params('place')
@api_view(["GET", "POST"])
def checkout_view(request):
	customer = Customer.objects.get(user=request.user)
	params = useParams(request)
	place = Restaurant.objects.get(slug=params.get('place'))
	cart = get_cart(customer, place)
	cart_items = cart.items.all()

	if request.method == "POST":
		order = Order(
			customer=customer,
			delivery_is_on=request.data.get('delivery', True),
			payment_id=request.data.get('receipt')['transaction_id'],
			invoice=request.data.get('receipt')['flutter_ref'],
			paid=True,
		)
		order.save()
		order.items.set(cart_items)
		order.save()

		cart.items.set([])
		cart.save()

		data = {
			'message': 'Successfully created your order',
			'order': OrderSerializer(order).data
		}
		return Response(data)

	total = (
		calc_subtotal(cart_items) +
		calc_deivery_fee(cart_items) +
		calc_vat(cart_items) + 
		calc_processing_fee(cart_items)
	)
	data = {
		'subtotal': str(round(calc_subtotal(cart_items), 2)),
		'fees': [
			{
				'type': 'Delivery fee',
				'amount': round(calc_deivery_fee(cart_items), 2)
			},
			{
				'type': 'Service fee',
				'amount': round(calc_processing_fee(cart_items), 2)
			},
			{
				'type': 'VAT',
				'amount': round(calc_vat(cart_items), 2)
			},
		],
		'items': OrderItemSerializer(cart_items.order_by('-id'), many=True, context={'request': request}).data,
		'total': str(round(total, 2))
	}
	return Response(data=data)


# @required_params('place')
@api_view(["GET", "POST"])
def leave_a_review(request):
	if request.method == "POST":
		review = Review(
			by=request.user,
			rating=request.data['stars'],
			food=FoodItem.objects.get(id=request.data['item']),
			comment=request.data['comment']
		)
		review.save()
		return Response(data={'error': None, 'response_text': 'Successfully reviewed item'})

	# GET : check if a user has reviewed this item
	try:
		review = Review.objects.get(
			by= request.user,
			food=FoodItem.objects.get(id=useParams(request).get('item', None)),
			)
		res = {
			'error': None,
			'user_has_review' : True,
			'reviews': ReviewSerializer(
				Review.objects.filter(
					food=FoodItem.objects.get(
						id = useParams(request).get('item', None)
					)),
				many=True).data
		}
	except Review.DoesNotExist:
		res = {
			'error': None,
			'user_has_review' : False,
			'reviews': ReviewSerializer(
				Review.objects.filter(
					food=FoodItem.objects.get(
						id = useParams(request).get('item', None)
					)),
				many=True).data

		}
	return Response(status=200, data=res)


@api_view(["GET"])
def notifications_view(request):
	try:
		nots = Notification.objects.filter(to=request.user.customer)
		_list = NotificationSerializer(nots, many=True).data
		return Response({'error': None, 'notifications': _list})
	except Exception as e:
		return Response({'error': True, 'error_text': str(e)})


@api_view(["GET"])
def user_account_view(request):
	try:
		person = Customer.objects.get(user=request.user)
		data = CustomerSerializer(instance=person).data
		print("Data:", data)
		return Response(data=data)
	except Exception as e:
		raise e
		return Response({ 'error': True, 'message' : str(e) })



@api_view(["GET"])
def user_account_orders_view(request):
	try:
		person = Customer.objects.get(user=request.user)
		return Response()
	except Exception as e:
		return Response({ 'error': True, 'message' : str(e) })



@api_view(["GET"])
def user_account_order_detail_view(request):
	try:
		person = Customer.objects.get(user=request.user)
		return Response()
	except Exception as e:
		return Response({ 'error': True, 'message' : str(e) })




