from functools import wraps
import os, json
from rest_framework.views import APIView
from rest_framework.generics import (
	CreateAPIView,
	ListAPIView,
	RetrieveUpdateDestroyAPIView,
	DestroyAPIView,
)
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



def get_featured_items():
	featured_items = FoodItem.objects.filter(featured=True)
	featured_items.order_by('?')[10]
	return


def generate_feed(food_items, liked_tags, follows):
	# no duplicates
	other_matches = set()
	recommendations = set()
	followed_matches = set()

	for tag in liked_tags:
		# find places that user follows matching this tag 
		for place in follows.filter(tags__icontains=tag.name):
			followed_matches.add(place) 
			# find products that match the tag in this place
			for match in place.menu.filter(tags__icontains=tag):
				recommendations.add(match)
			# find featured items in this place
			for featured in place.menu.filter(featured=True)[:2]:
				recommendations.add(featured)

		# find other places not followed by user that match
		for place in Restaurant.objects.filter(tags__icontains=tag):
			other_matches.add(place)
			for match in place.menu.filter(tags__icontains=tag):
				recommendations.add(match)
			# find featured items in this place
			for featured in place.menu.filter(featured=True)[:2]:
				recommendations.add(featured)

		# find general products that match tag
		for match in food_items.filter(tags__icontains=tag):
			recommendations.add(match)

	# @Todo
	# 1. Create a queryset from recommendations and filter by reviews,
	# order by 'id', 'price' 'popularity'
	# 
	# 2. Refine the recommendations with follows first, and 
	# others last
	# 
	return recommendations




# decorators
def required_params(*params):
	def decorator(main_view):
		@wraps(main_view)
		def view_handler(request, *args, **kwargs):
			for param in params:
				if not param in request.GET.keys():
					print("Param missing:", param)
					return Response(status=400, data={'error': f'{param} param missing'})
				else:
					return main_view(request, *args, **kwargs)
		return view_handler
	return decorator


def paginate_items(items, request, num_per_page=10):
	paginator = PageNumberPagination()
	paginator.page_size = num_per_page
	page_size_query_param = 'page_size'
	paginated_data = paginator.paginate_queryset(items, request)
	data = paginator.get_paginated_response(paginated_data).data
	return data


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

		token = Token.objects.create(user=user)
		customer_profile = Customer(
			user=user,
			phone=request.data['phone']
		)
		customer_profile.save()

		data = {
			'profile': {
				'user': UserSerializer(user).data,
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
		user_account = Account.objects.get(email=request.data['email'])
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
	except User.DoesNotExist as e:
		return Response(data={'error': True, 'message': 'User does not exist with this email!'}, status=404)


@api_view(["GET"])
def search_view(request):
	query = request.GET.get('query', None)
	_filter = request.GET.get('filter', None)

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



@api_view(["GET"])
@required_params('place')
def menu_feed_view(request):
	place = request.GET.get('place', None)
	user = request.user
	customer_profile = Customer.objects.get_or_create(user=user)[0]
	food_items = FoodItem.objects.all()

	# building recommendations
	follows = customer_profile.get_follows()
	liked_tags = customer_profile.get_liked_tags()
	featured_items = get_featured_items()
	
	# feed and pagination
	feed = generate_feed(food_items=food_items, tags=liked_tags, follows=follows)
	results = paginate_items(feed, request)

	try:
		page = dict(results)
		data = {
			'error': False,
			'data': {
				'products': FoodSerializer(page['results'], many=True).data,
				'categories': CategorySerializer(category.objects.all(), many=True).data,
				'featured_items': FoodSerializer(featured_items, many=True).data
			},
			'next_url': page['next'],
			'previous_url': page['previous'],
			'count': page['count'],
		}
		return Response(data=data, status=200)
	except Exception as e:
		return Response(data={'error': True, 'message': str(e)}, status=500)


@api_view(["GET"])
@required_params('place', 'foodId')
def item_detail_view(request, **kwargs):
	food_item = FoodItem.objects.get(itemid=kwargs['pk'])
	similar_items = get_simlar_items(food_item)
	res = {
		'food_item': FoodSerializer(food_item).data,
		'error': None
	}
	return Response(status=200, data=res)


@api_view(["GET", "POST"])
def cart_view(request):
	customer = Customer.objects.get(user=request.user)
	try:
		if request.method == "POST":
			if request.data['action'] == 'add-to-cart':
				food_item = FoodItem.objects.get(id=request.data['item'])
				order_item = OrderItem(item=food_item, qty=request.data.get('qty', 1))
				order_item.save()
				customer.cart.add(order_item)
				customer.save()

				if request.data.get('customizations', None):
					customizations = request.data['customizations']
					for custom in customizations:
						customization = Customization.objects.filter(food=food_item).get(title=custom)
						option = OrderCustomization(
							customization=customization,
							option=customization.options.all().get(
									option=customizations[custom]['option']
								))
						option.save()
						order_item.customizations.add(option)
					order_item.save()
					return Response({'error': None, 'response_text': 'Successfully added item to cart'})

			elif request.data['action'] == 'remove-from-cart':
				order_item = OrderItem.objects.get(
						id=request.data['item']
					)
				order_item.delete()
				return Response({'error': None, 'response_text': 'Successfully removed item from cart'})
		
		qs = customer.cart.all().order_by('-id')
		res = {
			'error': None,
			'subtotal': str(round(calc_subtotal(qs), 2)),
			"items": OrderItemSerializer(qs, many=True).data
		}
		return Response(data=res, status=200)
	except Exception as e:
		return Response(data={'error': True, 'error_text': str(e)}, status=200)


@api_view(["GET", "POST"])
@required_params('place')
def checkout_view(request):
	customer = request.user.customer
	if request.method == "POST":
		order = Order(
			owner=customer,
			delivery_is_on=request.data['delivery']
		)
		order.save()
		order.items.add(customer.orders.all())
		order.save()
		return Response(data=OrderSerializer(order).data)

	cart_items = customer.cart.all()
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
				'amount': str(round(calc_deivery_fee(cart_items), 2))
			},
			{
				'type': 'Service fee',
				'amount': str(round(calc_processing_fee(cart_items), 2))
			},
			{
				'type': 'VAT',
				'amount': str(round(calc_vat(cart_items), 2))
			},
		],
		'items': OrderItemSerializer(cart_items.order_by('-id'), many=True).data,
		'total': str(round(total, 2))
	}
	return Response(data=data)


@api_view(["GET", "POST"])
@required_params('place')
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
			food=FoodItem.objects.get(id=request.GET.get('item', None)),
			)
		res = {
			'error': None,
			'user_has_review' : True,
			'reviews': ReviewSerializer(
				Review.objects.filter(
					food=FoodItem.objects.get(
						id = request.GET.get('item', None)
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
						id = request.GET.get('item', None)
					)),
				many=True).data

		}
	return Response(status=200, data=res)



@api_view(["GET"])
@required_params('place')
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
		return Response()
	except Exception as e:
		return Response({ 'error': True, 'message' : str(e) })



@api_view(["GET"])
@required_params('place')
def user_account_orders_view(request):
	try:
		person = Customer.objects.get(user=request.user)
		return Response()
	except Exception as e:
		return Response({ 'error': True, 'message' : str(e) })



@api_view(["GET"])
@required_params('place')
def user_account_order_detail_view(request):
	try:
		person = Customer.objects.get(user=request.user)
		return Response()
	except Exception as e:
		return Response({ 'error': True, 'message' : str(e) })




