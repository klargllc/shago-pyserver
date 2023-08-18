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
from django.db.models import Q, QuerySet
from rest_framework.response import Response
from places.api.serializers import (
	FoodSerializer,
	CustomerSerializer,
	CategorySerializer,
	TagSerializer,
	OrderSerializer,
	OrderItemSerializer,
	StoreNotificationSerializer,
	OrderDetailSerializer,
	NotificationSerializer,
	ReviewSerializer,
	RestaurantDetailSerializer,
	UserSerializer,
	PermissionSerializer,
	RestaurantSerializer,
	BranchSerializer,
	StaffSerializer,
	MerchantSerializer
)
from django.contrib.auth import authenticate
from places.models import *
from accounts.models import (
	Merchant,
	Customer,
	Account as User,
	RestaurantStaff as Staff,
)
from utils import required_params, get_search_matches
from rest_framework.decorators import api_view, parser_classes
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from api.docs.dashboard import (
	RESOURCES_VIEW
)
from dateutil.utils import today
from dateutil.parser import parse
from django.utils.timezone import now, make_aware



def get_place_from_user(user):
	result = None
	try:
		owner = Merchant.objects.get(user=user)
		result = [owner.store, False, True]
	except Merchant.DoesNotExist:
		try:
			staff = Staff.objects.get(user=user)
			result = [staff.place, True, False]
		except Staff.DoesNotExist:
			pass
	return result


def get_perms(permlist) -> dict:
	perms = Permission.objects.all().filter(content_type__model__in=permlist)
	permMap = {}
	for item in perms:
		keys = list(permMap.keys())
		key = item.content_type.name
		if key in keys:
			permMap[key].append(item.name)
		else:
			permMap[key] = [item]
	return permMap


@api_view(["POST"])
def login_view(request):
	try:
		user = authenticate(email=request.data['email'], password=request.data['password'])
		if user:
			place_data = get_place_from_user(user)
			place = place_data[0]
			is_staff = place_data[1]
			is_owner = place_data[2]

			if place:
				if is_staff:
					staff = Staff.objects.get(user=user, place=place)
					branches = [staff.assigned_branch]
					main_branch = staff.assigned_branch
				elif is_owner:
					main_branch = place.main_branch
					branches = place.branches.all()
				else:
					branches = None
					main_branch = None

				data = {
					'user': UserSerializer(user).data,
					'token': Token.objects.get_or_create(user=user)[0].key,
					'place': RestaurantSerializer(place).data,
					'is_staff': is_staff,
					'is_owner': is_owner,
					'branches': [
						{
							'branch_name': branch.branch_name,
							'branch_id': branch.branch_id,
							'currency': branch.currency,
						} for (branch) in branches],
					'main_branch': {
						'branch_name': main_branch.branch_name,
						'branch_id': main_branch.branch_id,
						'currency': main_branch.currency,
					},
				}
				return Response({'error': False, 'data': data})
		return Response({'error': True, 'message': "The email and password combination is invalid."}, status=404)
	except Exception as e:
		# print(e)
		# raise e
		return Response({'error': True, 'message': str(e)}, status=500)


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
	
	results['food_items'] = {
		'key': 'food_item',
		'label': 'Food Items',
		'match': FoodSerializer(place.menu.filter(
			Q(name__icontains=query)|
			Q(name__iexact=query)
		), many=True, context={'request': request}).data
	}
	
	results['orders'] = {
		'key': 'order',
		'label': 'Orders',
		'match': OrderSerializer(place.orders.filter(
			Q(customer__user__first_name__icontains=query) |
			Q(customer__user__last_name__icontains=query) |
			Q(order_id__icontains = query) |
			Q(customer__user__first_name__iexact=query) |
			Q(customer__user__last_name__iexact=query) |
			Q(order_id__iexact = query)
		), many=True, context={'request': request}).data
	}

	results['categories'] = {
		'key': 'categories',
		'label': 'Categories',
		'match': CategorySerializer(place.categories.filter(
			Q(name__icontains=query) |
			Q(name__iexact=query)
		), many=True).data
	}

	results['staff'] = {
		'key': 'Staff',
		'label': 'Staff',
		'match': StaffSerializer(place.staff.filter(
			Q(user__first_name__icontains=query) |
			Q(user__last_name__icontains=query) |
			Q(user__email__icontains=query) |
			Q(user__first_name__iexact=query) |
			Q(user__last_name__iexact=query) |
			Q(user__email__iexact=query),
			staff_id__icontains=query,
		), many=True).data
	}
	
	results['customers'] = {
		'key': 'customers',
		'label': 'Customers',
		'match': CustomerSerializer(place.customers.filter(
			Q(user__first_name__icontains=query) |
			Q(user__last_name__icontains=query) |
			Q(user__email__icontains=query) |
			Q(user__first_name__iexact=query) |
			Q(user__last_name__iexact=query) |
			Q(user__email__iexact=query)
		), many=True).data
	}

	if filters:
		filters = filters.split(',')
	response = {
		'error': False,
		'matches': results
	}
	return Response(response)


@api_view(["GET"])
def resource_view(request):
	RESOURCES_VIEW

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
	allowed_methods = ['GET', 'POST']
	authentication_classes = [TokenAuthentication,]

	def get_recent_orders(self, place: Restaurant):
		recents = place.orders.all().order_by('-id')[:6]
		return recents

	def get_pending_orders_count(self, orders: QuerySet[Order]):
		orders = orders.filter(status='pending')
		return orders.count()

	def get_completed_orders_count(self, orders: QuerySet[Order]):
		orders = orders.filter(
			Q(closed=True, canceled=False) |
			Q(status='picked-up', canceled=False) |
			Q(status='canceled', canceled=False)
		)
		return orders.count()

	def get_canceled_orders_count(self, orders: QuerySet[Order]):
		orders = orders.filter(canceled=True)
		return orders.count()


	def get(self, request):
		orders = request.place.orders.all()
		recent_orders = self.get_recent_orders(request.place)
		recent_orders = OrderSerializer(recent_orders, many=True, context={'request': request}).data

		data = {
			'error': False,
			'recent_orders': recent_orders,
			'pending_orders': self.get_pending_orders_count(orders),
			'canceled_orders': self.get_canceled_orders_count(orders),
			'completed_orders': self.get_completed_orders_count(orders),
			'revenue': request.place.sales_revenue,
		}
		return Response(data=data)


@api_view(["GET", "POST", "DELETE"])
@required_params("place")
def categories_management_view(request, **kwargs):
	place:Restaurant = request.place
	cats = place.categories.all()

	if request.method == 'POST':
		action = request.data['action']

		if action == 'add':
			_cat = Category(name=request.data['name'])
			_cat.save()
			place.categories.add(_cat)
			place.save()
		elif action == 'change':
			_cat = place.categories.get(id=request.data['object_id'])
			_cat.name = request.data['name']
			_cat.save()
		elif action == 'remove':
			_cat = place.categories.get(name=request.data['name'])
			_cat.delete()
		else:
			return Response({ 'error': True, 'message': "Invalid operation command"})
	data = CategorySerializer(cats, many=True).data
	return Response({ 'data': data, 'error': False})


@required_params('place')
@parser_classes((MultiPartParser, ))
@api_view(["GET", "HEAD", "POST"])
def CreateFoodItemView(request, **kwargs):
	place = Restaurant.objects.get(slug=request.GET.get('place'))
	branch = place.branches.get(branch_id=request.GET.get('branch'))
	
	try:
		food_item = FoodItem(
			name=request.data['name'],
			price=request.data['price'],
			category=Category.objects.get(name=request.data['category']),
			about=request.data['about'],
			place=branch
		)
		food_item.save()
		branch.menu.add(food_item)
		branch.save()
		images = request.FILES.getlist('image')

		if images:
			for image in images:
				food_image = FoodImage(item=food_item, image=image)
				food_image.save()
				food_item.images.add(food_image)
			food_item.save()

		return Response({
			'error': None,
			'item': FoodSerializer(food_item, context={'request': request}).data
			}, 
			status=201
		)
	except Exception as e:
		# raise e
		return Response({'error': True, 'message': str(e)}, status=500)


class EditFoodItemView(RetrieveUpdateDestroyAPIView):
	serializer_class = FoodSerializer
	lookup_field = 'slug'
	lookup_url_kwarg = 'itemId'

	def get_queryset(self, **kwargs):
		place = Restaurant.objects.get(slug=self.request.GET.get('place'))
		branch = place.branches.get(branch_id=self.request.GET.get('branch'))
		qs = branch.menu.all()
		return qs

	def delete(self, request, **kwargs):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		branch = place.branches.get(branch_id=request.GET.get('branch'))
		food_item:FoodItem = branch.menu.get(slug=kwargs['itemId'])
		food_item.delete()
		return Response({'error': False, 'message': "Successfully deleted food item"})

	def post(self, request, **kwargs):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		branch = place.branches.get(branch_id=request.GET.get('branch'))
		food_item = branch.menu.get(slug=kwargs['itemId'])
		action = request.data.get('action', None)
		data = FoodSerializer(food_item, context={'request': request}).data
		
		if action and action == "remove-choice":
			pass # del the customization
		elif action and action == "remove-option":
			pass # del a customization option
		elif action and action == "remove-image": # remove an image
			print("Deleteing Image")
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


class MenuView(ListAPIView):
	model = FoodItem
	serializer_class = FoodSerializer
	place = None
	authentication_classes = [TokenAuthentication,]

	def get_place(self, request):
		if not self.place:
			self.place = Restaurant.objects.get(slug=request.GET.get('place'))
		return self.place
	
	def get_branch(self, request):
		branch = self.place.branches.get(branch_id=request.GET.get('branch'))
		self.branch = branch
		return branch

	def get_queryset(self):
		queryset = self.branch.menu.all()
		return queryset

	def get(self, request):
		try:
			self.get_place(request)
			self.get_branch(request)
			menu = self.get_queryset()

			if request.GET.get('find', None):
				menu = menu.filter()
			
			data = {
				'error': None,
				'data': FoodSerializer(menu, many=True, context={'request': request}).data,
			}
		except Exception as e:
			raise e
			data = {
				'error': True,
				'data': e,
			}
		return Response(data)

	def delete(self, request, slug):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		branch = place.branches.get(branch_id=request.GET.get('branch'))
		for item in request.data.get('items', None):
			food = branch.menu.get(slug=item)
			food.delete()
		return Response({'error': None, 'message': 'Successfully deleted products'})


class CreateOrderView(CreateAPIView):
	serializer_class = OrderSerializer
	
	def get(self, request):
		place:Restaurant = request.place
		branch = place.branches.get(branch_id=request.GET.get('branch'))
		data = {
			'error': None,
			'products': FoodSerializer(branch.menu.all(), many=True, context={'request': request}).data,
			'customers': CustomerSerializer(place.customers.all(), many=True).data,
		}
		return Response(data, status=200)


	def post(self, request, **kwargs):
		print("ORDER DATA:", request.data)
		# raise Exception("Data")
		try:
			place:Restaurant = request.place
			branch:RestaurantBranch = place.branches.get(branch_id=request.GET.get('branch'))
			data = request.data
			_user = User.objects.get(email=data['customer'])
			customer = Customer.objects.get(user=_user)
			order = Order(
				customer=customer,
				delivery_is_on=data['deliveryOption'] == 'delivery',
				place_id=place,
				branch_id=branch,
				status=request.data['status'],
				created_on=make_aware((parse(data['timeOfOrder']))),
				paid=data['paymentStatus'],
			)
			if data.get('pickupTime', None):
				order.pickup_time=data['pickupTime']
			order.save()

			for item in data['orderItems']:
				order_item = OrderItem(
					item = branch.menu.get(slug=item['item']),
					quantity = item['quantity'],
				)
				order_item.save()

				customizations = item.get('customizations', None)
				if customizations:
					for customization in customizations:
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
			customer.orders.add(order);	place.orders.add(order); branch.related_orders.add(order)
			place.save(); branch.save(); customer.save()
			return Response({'error': None, 'order': OrderSerializer(order, context={'request': request}).data}, status=201)
		except Exception as e:
			raise e
			return Response({'error': True, 'message': str(e)}, status=500)


class OrderDetailView(APIView):
	serializer_class = OrderSerializer

	def get(self, request, orderId, *args, **kwargs):
		try:
			place:Restaurant = request.place
			branch = place.branches.get(branch_id=request.GET.get('branch'))
			order = branch.related_orders.get(order_id=orderId)
			data = {
				'error': None,
				'order': OrderDetailSerializer(order, context={'request': request}).data
			}
			return Response(data)
		except Exception as e:
			raise e
			data = {'error': True, 'message': str(e)}
			return Response(data)
	
	def post(self, request, orderId, *args, **kwargs):
		print("Got Data:", request.data)
		try:
			place:Restaurant = request.place
			branch = place.branches.get(branch_id=request.GET.get('branch'))
			order:Order = branch.related_orders.get(order_id=orderId)
			action = request.data['action']

			if action == 'change-order-status':
				order.status = request.data['status']
				if request.data['status'] in ['delivered', 'pickup']: # delivered or picked-up
					order.delivered = True
					order.closed = True
				order.save()
			elif action == 'change-payment-status':
				order.paid = request.data['status']
				order.save()
			elif action == 'cancel-order':
				order.canceled = True
				order.closed = True
				order.save()
			else:
				raise Exception("Invalid parameter options")
			return Response({'error': False, 'order': OrderSerializer(order, context={'request': request}).data})
		except Exception as error:
			raise error
			return Response({ 'error': True, 'message': str(error)}, 500)

	def delete(self, request, orderId):
		return Response()


class ListOrdersView(ListAPIView):

	serializer_class = OrderSerializer

	def post(self, request):
		place:Restaurant = request.place
		action = request.data['action']
		items = request.data['items']

		if action == 'delete':
			for item in items:
				order = place.orders.get(order_id=item)
				order.delete()
		return Response({'error': False, 'message': "Successfully deleted order"})

	def get(self, request):
		place:Restaurant = request.place
		branch = place.branches.get(branch_id=request.GET.get('branch'))
		orders = OrderSerializer(
			branch.related_orders.all().order_by('-id'),
			many=True,
			context={'request': request}
		).data
		data = {
			'error': None,
			'orders': orders
		}
		return Response(data)


class ListCustomersView(ListAPIView):
	serializer_class = CustomerSerializer

	model = Customer

	def get_queryset(self, request, **kwargs):
		place:Restaurant = request.place
		print(request)
		return place.customers.all()

	def get(self, request, **kwargs):
		try:
			customers = self.get_queryset(request)
			data = self.serializer_class(customers, many=True).data
			return Response({ 'error': False, 'data': data})
		except Exception as e:
			return Response({ 'error' : True, 'message': str(e)}, status=500)


class CreateCustomerView(APIView):
	def post(self, request, *args, **kwargs):
		try:
			new_user = User(
				first_name=request.data['first_name'],
				last_name=request.data['last_name'],
				email=request.data['email'],
			)
			new_user.set_unusable_password()
			new_user.save()

			customer = Customer(
				user=new_user,
				phone=request.data['phone']
			)
			customer.save()
			place:Restaurant = request.place
			place.customers.add(customer,)
			place.save()

			return Response({'error': False, 'customer': CustomerSerializer(customer).data}, status=201)
		except Exception as error:
			raise error
			return Response({'error': True, 'message': str(error)}, status=500)


class ListStaffView(ListAPIView):
	authentication_classes = [TokenAuthentication]
	serializer_class = StaffSerializer

	def get(self, request):
		print("Profile:", request.profile)
		place:Restaurant = request.place
		all_staff = place.staff.all()
		data = {
			'error': None,
			'data': StaffSerializer(all_staff, many=True).data
		}
		return Response(data)


class CreateStaffView(APIView):
	serializer_class = StaffSerializer
	authentication_classes = [TokenAuthentication]


	# @required_params('get')
	def get(self, request):
		permlist = get_perms([
			'category',
			'fooditem',
			'restaurantstaff',
			'order',
			'customer'
		])
		data = {
			'error': False,
			'roles': [
				{'role' : 'admin', 'label' : 'Admin'},
				{'role' :'site-manager', 'label': 'Site Manager'}
			],
			'branches': [
				{
					'branch_id': branch.branch_id,
					'branch_name': branch.branch_name
				} for (branch) in request.place.branches.all()
			]
		}
		return Response(data)

	def post(self, request):
		try:
			print(request.data)
			# raise ""
			place = Restaurant.objects.get(slug=request.GET.get('place'))
			user = User(
				email=request.data['email'],
				first_name=request.data['first_name'],
				last_name=request.data['last_name'],
			)
			user.set_unusable_password()
			user.save()

			branch = place.branches.get(branch_id=request.data['branch'])
			staff = Staff(
				user=user,
				place=place,
				role=request.data['role'],
				assigned_branch=branch
			)
			staff.save()

			branch.assigned_staff.add(staff,)
			place.staff.add(staff,)
			place.save(); branch.save()
			return Response({'error': None, 'staff': StaffSerializer(staff).data}, status=201)
		except Exception as e:
			# raise e
			return Response({'error': None, 'message': str(e)})


class ChangeStaffView(APIView):
	serializer_class = StaffSerializer

	def get(self, request, *args, **kwargs):
		try:
			staffId = kwargs['staffId']
			staff = Staff.objects.get(staff_id=staffId, place=request.place)
			permlist = get_perms([
				'category',
				'fooditem',
				'restaurantstaff',
				'order',
				'customer'
			])
			data = {
				'error': False,
				'roles': [
					{'role' : 'admin', 'label' : 'Admin'},
					{'role' :'site-manager', 'label': 'Site Manager'}
				],
				'staff': StaffSerializer(staff).data,
				'branches': [
					{
						'branch_id': branch.branch_id,
						'branch_name': branch.branch_name
					} for (branch) in request.place.branches.all()
				]
			}
			return Response(data)
		except Exception as error:
			raise error
			return Response({'error': True, 'message': str(error)}, status=500)

	def post(self, request, *args, **kwargs):
		try:
			edit = False
			place = request.place
			action = request.data.get('action', None)
			staff = Staff.objects.get(place=place, staff_id=kwargs['staffId'])

			if action == 'remove':
				staff.delete()
				return Response({'error': False, 'message': "Successfully deleted Staff account"})
			elif action == 'change':
				if not request.data['role'] == staff.role:
					staff.role = request.data['role']
					edit = True
				if staff.assigned_branch:
					if not request.data['branch'] == staff.assigned_branch.branch_id:
						oldbranch = staff.assigned_branch
						oldbranch.assigned_staff.remove(staff)
						oldbranch.save()
				
				branch = place.branches.get(branch_id=request.data['branch'])
				branch.assigned_staff.add(staff)
				staff.assigned_branch = branch
				branch.save()
				edit = True
				if edit:staff.save()
			return Response({'error': False, 'staff': StaffSerializer(staff).data}, status=200)
		except Exception as e:
			return Response({'error': False, 'message': str(e)})


class ListNotificationsView(ListAPIView):
	queryset = Customer.objects.all()
	serializer_class = NotificationSerializer

	def get(self, request):
		notifications = StoreNotificationSerializer(NotificationMessage.objects.filter(
			place_id=request.place,
			branch_id=request.place.branches.get(branch_id=request.GET.get('branch'))
		), many=True).data
		data = {
			'error': None,
			'notifications': notifications
		}
		return Response(data)


class ListBranchView(APIView):

	def get(self, request):
		place = request.place
		branches = place.branches.all()
		branch_data = BranchSerializer(branches, many=True, context={'request': request}).data
		return Response({'error': False, 'branches': branch_data})

	def post(self, request):pass


class ManageBranchView(APIView):
	def get(self, request, *args, **kwargs):
		place:Restaurant = request.place
		branch = place.branches.get(branch_id=kwargs.get('branchId'))
		response_data = {
			'branch_quota': place.branch_quota,
			'branch': BranchSerializer(branch, context={'request': request}).data,
		}
		return Response({'error': False, 'data': response_data})

	def post(self, request, *args, **kwargs):
		place:Restaurant = request.place
		branchId = kwargs.get('branchId', None)
		data = request.data


class CreateBranchView(APIView):
	def get(self, request, *args, **kwargs):
		place:Restaurant = request.place
		branch_quote = place.branch_quota
		branches = place.branches.count()
		can_create_branch = (branch_quote > branches)
		return Response({
			'error': False,
			'branch_qouta': branch_quote,
			'can_create_branch': can_create_branch,
		})

	def post(self, request, *args, **kwargs):
		place:Restaurant = request.place
		branchId = kwargs.get('branchId', None)
		data = request.data
		print("DATA:", data)
		# creating a new branch
		can_create_branch = (place.branch_quota > place.branches.count())
		if not can_create_branch:
			return Response({ 'error': True, 'message': "Branch limit exceeded" }, 400)
		
		# raise Exception
		branch = place.branches.get(branch_id=data['inherit_source'])
		new_branch = RestaurantBranch(
			branch_name = data['branch_name'],
			offer_delivery = data['offer_delivery'],
			offer_pickup = data['offer_pickup'],
			offer_dine_in = data['offer_dine_in'],
			inherit_menu = data['inherit_menu'],
			country = data['country'],
			currency = data['currency'],
			place_id=place,
			inherit_menu_from=branch
		)
		new_branch.save()
		place.branches.add(new_branch,)
		place.save()
		return Response({}, 200)


# Settings View (Superuser only)
class ManagerView(APIView):
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		data = RestaurantDetailSerializer(place, context={'request': request}).data
		return Response({'error': False, 'data': data})

	def post(self, request):
		try:
			target = request.GET.get('target', None)

			# if not target:
			# 	return Response({'error': True, 'message': 'specify resource param with ?target=<resource>'}, status=500)
			
			if target == 'restaurant:logo':
				self.handle_logo_change(request.data)
			elif target == 'restaurant:banner':
				self.handle_banner_change(request.data)
			elif target == 'restaurant:description':
				self.handle_description_change(request.data)
			return Response(status=200)
		except Exception as error:
			print("An error occured:", error)
			return Response({'error': True, 'message': str(error)})


	def handle_logo_change(self, data=None):
		place:Restaurant = self.request.place
		place.logo = self.request.data['logo']
		place.save()

	def handle_banner_change(self, data=None):
		place:Restaurant = self.request.place
		place.banner = self.request.data['banner']
		place.save()

	def handle_description_change(self, data):
		place:Restaurant = self.request.place
		place.about = data['about']
		place.save()

	
	def handle_billing_change(self, data):pass

	def handle_payout_change(self, data):pass

	def handle_featured_items_change(self, data):pass

	def handle_domain_change(self, data):pass




