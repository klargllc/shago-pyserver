import os, json
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import (
	CreateAPIView,
	ListAPIView,
	RetrieveUpdateDestroyAPIView,
	DestroyAPIView,
)
from rest_framework.parsers import (MultiPartParser, )
from django.db.models import Q
from rest_framework.response import Response
from places.api.serializers import (
	FoodSerializer,
	CustomerSerializer,
	CategorySerializer,
	TagSerializer,
	OrderSerializer,
	OrderItemSerializer,
	ReviewSerializer,
	UserSerializer,
	PermissionSerializer,
	RestaurantSerializer,
	StaffSerializer,
)
from django.contrib.auth import authenticate
from places.models import *
from accounts.models import (
	BusinessAccount,
	Customer,
	Account as User,
	RestaurantStaff as Staff,
)
from utils import required_params
from rest_framework.decorators import api_view, parser_classes


def get_place_from_user(user):
	place = None
	try:
		owner = BusinessAccount.objects.get(user=user)
		place = (owner, owner.store)
	except BusinessAccount.DoesNotExist:
		pass
	try:
		staff = Staff.objects.get(user=user)
		if staff in place.staff.all():
			place = (staff, staff.place)
	except Staff.DoesNotExist:
		pass
	return place


@api_view(["POST"])
def login_view(request):
	try:
		user = authenticate(
			email=request.data['email'],
			password=request.data['password']
		)

		if user:
			person, place = get_place_from_user(user)
			if place:
				place = RestaurantSerializer(place).data
			data = {
				'user': UserSerializer(user).data,
				'token': Token.objects.get_or_create(user=user)[0].key,
				'place': place
			}
			return Response({'error': False, 'data': data})

		return Response({'error': True, 'message': "User not found"}, status=404)
	except Exception as e:
		print("ERROR:", e)
		raise e
		return Response({'error': True, 'message': str(e)}, status=404)

@api_view(["GET"])
@required_params('place', 'query')
def search_view(request):
	params = request.GET
	place = Restaurant.objects.get(slug=params.get('place'))
	query = params.get('query', None)
	filters = params.get('filters', None)
	sort = params.get('sort-by', None)
	results = {}

	if not query:
		return Response({'error': True, 'message': 'query missing from search params'}, status=400)
	else:
		results['customers'] = {
			'key': 'Customers',
			'label': 'Customers',
			'match': CustomerSerializer(place.customers.all(), many=True).data
		}

		# results['results'] = [
		# 	{
		# 		'key': 'Menu Items',
		# 		'match': FoodSerializer(place.menu.all(), many=True).data
		# 	},
		# 	{
		# 		'key': 'Staff',
		# 		'match': StaffSerializer(place.staff.all(), many=True).data
		# 	},
		# 	{
		# 		'key': 'Orders',
		# 		'match': OrderSerializer(place.orders.all(), many=True).data
		# 	},
		# ]
	if filters:
		filters = filters.split(',')
	if sort:
		pass

	response = {
		'error': False,
		'matches': results
	}
	return Response(response)


@api_view(["GET"])
def resource_view(request):
	"""
		## Get resources required to perform any API transaction
		
		Example:
			- Categories
			- Staff
			- Orders
			- Customers
	"""
	target = request.GET['target'] or None
	org = request.GET['place'] or None
	if not target and not org:
		return Response(status=400, data={'error': True, 'message': 'Please specify an org and a target.'})
	res = None
	place = Restaurant.objects.get(slug=org)
	if target == 'Categories':
		res = CategorySerializer(place.categories.all(), many=True).data
	elif target == 'Customers':
		res = CustomerSerializer(Customer.objects.all(), many=True).data
	return Response(status=200, data={'data': res, 'error': False})

class DashboardView(APIView):
	def get(self, request):
		data = {
			'help': None,
		}
		return Response(data=data)


@api_view(["GET", "POST", "DELETE"])
@required_params("place")
def categories_management_view(request, **kwargs):
	org = request.GET.get('place')
	place = Restaurant.objects.get(slug=org)
	cats = place.categories.all()

	if request.method == 'POST':
		action = request.data['action']

		if action == 'add':
			_cat = Category(name=request.data['name'])
			_cat.save()
			place.categories.add(_cat)
			place.save()
			pass
		elif action == 'change':
			_cat = place.categories.get(id=request.data['object_id'])
			_cat.name = request.data['name']
			_cat.save()
			pass
		elif action == 'remove':
			_cat = place.categories.get(name=request.data['name'])
			_cat.delete()
			pass
		else:
			return Response({ 'error': True, 'message': "Invalid operation command"})
	data = CategorySerializer(cats, many=True).data
	return Response({ 'data': data, 'error': False})


@required_params('place')
@parser_classes((MultiPartParser, ))
@api_view(["GET", "HEAD", "POST"])
def CreateFoodItemView(request, **kwargs):
	place = Restaurant.objects.get(slug=request.GET.get('place'))
	
	try:
		food_item = FoodItem(
				name=request.data['name'],
				price=request.data['price'],
				category=Category.objects.get(name=request.data['category']),
				about=request.data['about'],
				place=place
			)
		food_item.save()
		place.menu.add(food_item)
		place.save()
		images = request.FILES.getlist('image')

		if images:
			for image in images:
				food_image = FoodImage(item=food_item, image=image)
				food_image.save()
				food_item.images.add(food_image)
			food_item.save()

		return Response({'error': None, 'item': FoodSerializer(food_item).data}, status=201)
	except Exception as e:
		raise e
		return Response({'error': True, 'message': str(e)}, status=500)


class EditFoodItemView(RetrieveUpdateDestroyAPIView):
	serializer_class = FoodSerializer
	lookup_field = 'slug'

	def get_queryset(self, **kwargs):
		place = Restaurant.objects.get(slug=self.request.GET.get('place'))
		qs = place.menu.all()
		return qs

	def delete(self, request, **kwargs):
		print("KWARGS:", kwargs)
		place = Restaurant.objects.get(slug=self.request.GET.get('place'))
		food_item = place.menu.get(slug=kwargs['slug'])
		food_item.delete()
		return Response({'error': False, 'message': "Successfully deleted food item"})

	def post(self, request, **kwargs):
		place = Restaurant.objects.get(slug=self.request.GET.get('place'))
		food_item = place.menu.get(slug=kwargs['slug'])
		action = request.data.get('action', None)
		data = FoodSerializer(food_item).data
		
		if action and action == "remove-choice":
			pass # del the customization
		elif action and action == "remove-option":
			pass # del a customization option
		elif action and action == "remove-image": # remove an image
			img = food_item.images.get(id=request.data['object_id'])
			img.delete()
		else: # saving the product changes
			food_item.name = request.data['name']
			food_item.about = request.data['about']
			food_item.category = place.categories.get(name=request.data['category'])
			food_item.price = request.data['price']

			images = request.FILES.getlist('image')
			if images and food_item.images.count() < 3:
				for image in images:
					food_image = FoodImage(item=food_item, image=image)
					food_image.save()
					food_item.images.add(food_image)
			food_item.save()
		return Response({'error': None, 'data': data})


class ListFoodItemView(ListAPIView):
	model = FoodItem
	serializer_class = FoodSerializer
	place = None

	def get_place(self, request):
		if not self.place:
			self.place = Restaurant.objects.get(slug=request.GET.get('place'))
		return self.place

	def get_queryset(self):
		queryset = self.model.objects.all().filter(place=self.place)
		return queryset

	def get(self, request):
		self.get_place(request)
		menu = self.get_queryset()

		if request.GET.get('find', None):
			menu = menu.filter()
		data = {
			'error': None,
			'data': FoodSerializer(menu, many=True).data,
		}
		return Response(data)

	def delete(self, request, slug):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		for item in request.data.get('items', None):
			food = place.menu.get(slug=item)
			food.delete()
		return Response({'error': None, 'message': 'Successfully deleted products'})


class CreateOrderView(CreateAPIView):
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		data = {
			'error': None,
			'products': FoodSerializer(place.menu.all(), many=True).data,
			'customers': CustomerSerializer(place.customers.all(), many=True).data,
		}
		return Response(data, status=200)


	def post(self, request, **kwargs):
		try:
			place = Restaurant.objects.get(slug=request.GET.get('place'))
			data = request.data
			_user = User.objects.get(email=data['customer'])
			customer = place.customers.get(user=_user)
			order = Order(
					customer=customer,
					delivery_is_on=True if data.get('delivery', None) == 'delivery' else False,
				)
			order.save()

			for item in data['orderItems']:
				order_item = OrderItem(
					item = place.menu.get(slug=item['item']),
					quantity = item['quantity'],
				)
				order_item.save()

				customizations = item.get('customizations', None)
				if customizations:
					for customization in customizations:
						print("Customization:", customization)
						custom = Customization.objects.get(title=customization['customize'], food=order_item.item)
						option = CustomizationOption.objects.get(to=custom, option=customization['choice'])
						customize = OrderCustomization(
							customization = custom,
							option = option
						)
						customize.save()
						order_item.customizations.add(customize)
						order_item.save()
				order.items.add(order_item)
			order.save()
			customer.orders.add(order)
			place.orders.add(order)
			place.save()
			customer.save()
			return Response({'error': None, 'order': OrderSerializer(order).data}, status=201)
		except Exception as e:
			raise e
			return Response({'error': True, 'message': str(e)}, status=500)


class OrderDetailView(APIView):
	def get(self, request, invoice):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		try:
			order = place.orders.get(invoice=invoice)
			data = {
				'error': None,
				'order': OrderSerializer(order).data
			}
			return Response(data)
		except Exception as e:
			data = {'error': True, 'message': str(e)}
			return Response(data)


class ListOrdersView(ListAPIView):

	def delete(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		for item in request.data['items']:
			order = place.orders.get(id=item)
			order.delete()
		return Response({'error': False, 'message': "Successfully deleted order"})

	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		orders = OrderSerializer(place.orders.all().order_by('-id'), many=True).data
		data = {
			'error': None,
			'orders': orders
		}
		return Response(data)


class ListCustomersView(ListAPIView):
	serializer_class = CustomerSerializer
	model = Customer

	def get_queryset(self, request, **kwargs):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		return place.customers.all()

	def get(self, request, **kwargs):
		try:
			customers = self.get_queryset()
			data = self.serializer_class(customers, many=True).data
			print("DATA:", data)
			return Response({ 'error': False, 'data': data})
		except Exception as e:
			return Response({ 'error' : True, 'message': str(e)})


class ListStaffView(ListAPIView):
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		all_staff = place.staff.all()
		data = {
			'error': None,
			'data': StaffSerializer(all_staff, many=True).data
		}
		return Response(data)


class CreateStaffView(APIView):

	# @required_params('get')
	def get(self, request):
		perms = Permission.objects.all().filter(
			content_type__model__in=[
			'fooditem',
			'staff',
			'order',
			'customer'
			])

		req = request.GET.get('get')

		if req == 'roles':
			data = {
				'error': False,
				'roles': ['Admin', 'Site Manager', 'Customer Response'],
			}
		elif req == 'perms':
			data = {
				'error': False,
				'permissions': PermissionSerializer(perms, many=True).data
			}
		return Response(data)

	def post(self, request):
		try:
			print("Data Received:", request.data)
			place = Restaurant.objects.get(slug=request.GET.get('place'))
			staff_id = generate_staff_id()
			user = User(
					email=request.data['email'],
					first_name=request.data['first_name'],
					last_name=request.data['last_name'],
				)
			user.save()
			user.set_unusable_password()

			Staff(user=user, place=place).save()
			place.staff.add(staff)
			place.save()
			return Response({'error': None, 'staff': StaffSerializer(staff).data}, status=201)
		except Exception as e:
			raise e
			return Response({'error': None, 'message': str(e)})


class ListNotificationsView(ListAPIView):
	queryset = Customer.objects.all()
	serializer_class = CustomerSerializer

	def get(self, request):
		customers = CustomerSerializer(Customer.objects.all(), many=True).data
		data = {
			'error': None,
			'results': customers
		}
		return Response(data)

# Settings View (Superuser only)
class ManagerView(APIView):
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		data = RestaurantSerializer(place).data
		return Response({'error': False, 'data': data})

	def post(self, request):
		target = request.GET.get('target', None)
		action = request.data.get('action', None)

		if not target:
			return Response({'error': True, 'message': 'specify resource param with ?target=<resource>'}, status=500)
		if not action:
			return Response({'error': True, 'message': 'specify action in your request'}, status=500)
		return Response(status=500)


