import os, json
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import (
	CreateAPIView,
	ListAPIView,
	RetrieveUpdateDestroyAPIView,
	DestroyAPIView,
)
from rest_framework.authentication import (
	TokenAuthentication,
	BasicAuthentication
)
from rest_framework.parsers import (MultiPartParser, )
from django.db.models import Q
from rest_framework.response import Response
from django.contrib.auth.decorators import (login_required)
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
	BranchSerializer
)
from django.contrib.auth import authenticate
from places.models import *
from accounts.models import (
	Merchant,
	Customer,
	Account as User,
	RestaurantStaff as Staff,
)
from utils import required_params
from rest_framework.decorators import (
	api_view, parser_classes,
)


def get_place_from_user(user):
	place = None
	try:
		owner = Merchant.objects.get(user=user)
		place = owner.store
	except Merchant.DoesNotExist:
		pass
	try:
		staff = Staff.objects.get(user=user)
		if staff in place.staff.all():
			place = staff.place
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
			is_owner = False
			place:Restaurant = get_place_from_user(user)

			try:
				merchant = Merchant.objects.get(user=user)
				if place.owner == merchant:
					is_owner = True
					role = 'owner'
			except:
				staff = place.staff.get(user=user)
				role = staff.role.name
				is_owner = False

			try:
				if place:
					data = {
						'user': UserSerializer(user).data,
						'token': Token.objects.get_or_create(user=user)[0].key,
						'role': role,
						'place': RestaurantSerializer(place).data,
						'main_branch': {
							'branch_name': place.main_branch.branch_name,
							'branch_id': place.main_branch.branch_id,
						},
						'branches': BranchSerializer(place.branches, many=True).data,
						'is_owner': is_owner,
					}
					return Response({'error': False, 'data': data})
				else:
					data = {
						'error': True,
						'message': 'No Restaurant Access Found'
					}
					return Response(data, 400)
			except Exception as error:
				return Response({ 'error': True, 'message': str(error)}, 400)

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
		res = CustomerSerializer(place.customers.all(), many=True).data
	elif target == 'RestaurantBranch':
		res = BranchSerializer(place.branches.all(), many=True).data
	return Response(status=200, data={'data': res, 'error': False})


class DashboardView(APIView):
	def get(self, request):
		try:
			place = Restaurant.objects.get(slug=request.GET.get('place'))
			recent_orders = OrderSerializer(place.orders.all().order_by('-id')[:10], many=True, context={'request': request}).data
			data = {
				'help': None,
				'recent_orders': recent_orders
			}
			return Response(data=data)
		except Exception as error:
			print("error:", error)
			return Response(data={'error': True, 'message': str(error)})


class ManageCategoriesView(APIView):
	allowed_methods = ["GET", "POST", "HEAD", "OPTIONS", "DELETE"]
	@required_params("place")
	def get(self, request, **kwargs):
		org = request.GET.get('place')
		place = Restaurant.objects.get(slug=org)
		cats = place.categories.all()
		data = CategorySerializer(cats, many=True).data
		return Response({ 'data': data, 'error': False})


	@required_params("place")
	def post(self, request, **kwargs):
		place = request.place
		action = request.data['action']
		cats = place.categories.all()
		if action == 'add':
			_cat = Category(name=request.data['name'])
			_cat.save()
			place.categories.add(_cat)
			place.save()
		elif action == 'change':
			_cat = place.categories.get(id=request.data['object_id'])
			_cat.name = request.data['name']
		elif action == 'remove':
			_cat = place.categories.get(name=request.data['name'])
			_cat.delete()
		else:
			return Response({ 'error': True, 'message': "Invalid operation command"})
		data = CategorySerializer(cats, many=True).data
		return Response({ 'data': data, 'error': False})
	
		

# Food Item Handlers
class CreateFoodItemView(APIView):
	parser_classes = [MultiPartParser]
	allowed_methods = ["GET", "HEAD", "POST"]

	@required_params('place')
	def post(self, request, **kwargs):
		place = request.place
		branch = request.branch
		customizations = json.loads(request.data['customizations'])

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
			
			if request.data['availability'] == 'select-stores':
				# add to specific branches
				pass

			# branch.menu.add(food_item)
			# branch.save()

			if customizations:
				for custom in customizations:
					order_option = OrderOption(
						food_item = food_item,
						name = custom['name'],
					)
					order_option.save()

					# create and add each option
					for choice in custom['options']:
						option = CustomOptionChoice(
							customization=order_option,
							name=choice['name'],
							price=choice['price']
						)
						option.save()
						order_option.choices.add(option,)
						
						# set the default choice
						if choice['is_default']:
							order_option.default_choice = option
						order_option.save()

				food_item.custom_choices.add(order_option,)
				food_item.save()

			images = request.FILES.getlist('image')
			if images:
				for image in images:
					food_image = FoodImage(item=food_item, image=image)
					food_image.save()
					food_item.images.add(food_image)
				food_item.save()

			return Response({'error': None, 'item': FoodSerializer(food_item, context={'request': request}).data}, status=201)
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

	@required_params('place')
	def post(self, request, **kwargs):
		place = Restaurant.objects.get(slug=self.request.GET.get('place'))
		food_item: FoodItem = place.menu.get(slug=kwargs['slug'])
		action = request.data.get('action', None)
		data = FoodSerializer(food_item, context={'request': request}).data

		print("Change:", request.data)
		try:
			if action and action == "remove-custom-choice":
				option = food_item.custom_choices.get(id=request.data['object_id'])
				option.delete()
			elif action and action == "remove-image": # remove an image
				img = food_item.images.get(id=request.data['object_id'])
				img.delete()
			else: # action isn't provided, so save changes directly to the object
				food_item.name = request.data['name']
				food_item.about = request.data['about']
				food_item.category = place.categories.get(name=request.data['category'])
				food_item.price = request.data['price']

				# Moved to v2.0

				# availability = request.data['availability']
				# if availability == 'select-stores':
				# 	select_stores = request.data.get('stores', None)
				# 	place.branches.in_bulk
				# 	for location in select_stores:
				# 		branch:RestaurantBranch = place.branches.get(branch_id=location)
				# 		branch.menu.add(food_item,)
				# 		branch.save()
					

				
				customizations = request.data.get('customizations', None)
				if customizations:
					customizations = json.loads(customizations)
					
					for custom in customizations:
						print("Creating Customization", custom)
						
						# raise Exception
						if custom.get('id', None):
							# if the customization has an id, then it exists
							# hence, do nothing!
							print("Found Customization!")
							pass
						else: # create the customization
							print("Creating Customization!")
							order_option = OrderOption(
								food_item = food_item,
								name = custom['name'],
							)
							order_option.save()

							# create and add each option
							for choice in custom['choices']:
								option = CustomOptionChoice(
									customization=order_option,
									name=choice['name'],
									price=choice['price']
								)
								option.save()
								
								# set the default choice
								if choice['is_default']:
									order_option.default_choice = option

								order_option.choices.add(option,)
								order_option.save()

							food_item.custom_choices.add(order_option,)
							food_item.save()

				images = request.FILES.getlist('image')
				if images and food_item.images.count() < 3:
					for image in images:
						food_image = FoodImage(item=food_item, image=image)
						food_image.save()
						food_item.images.add(food_image)
				food_item.save()
			return Response({'error': None, 'data': data})
		except Exception as error:
			return Response({'error': True, 'message': str(error)})



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
			'data': FoodSerializer(menu, many=True, context={'request': request}).data,
		}
		return Response(data)

	def delete(self, request, slug):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		for item in request.data.get('items', None):
			food = place.menu.get(slug=item)
			food.delete()
		return Response({'error': None, 'message': 'Successfully deleted products'})


# Order Handlers
class CreateOrderView(CreateAPIView):

	@required_params('place')
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		data = {
			'error': None,
			'products': FoodSerializer(place.menu.all(), many=True, context={'request': request}).data,
			'customers': CustomerSerializer(place.customers.all(), many=True).data,
		}
		return Response(data, status=200)

	@required_params('place', 'branch')
	def post(self, request, **kwargs):
		try:
			place = request.place
			branch = request.branch
			data = request.data
			print("Data:", data)
			_user = User.objects.get(email=data['customer'])
			customer = place.customers.get(user=_user)

			order = Order(
				branch_id=branch,
				place_id=place,
				customer=customer,
				status=data['status'],
				payment_status=data['payment_status'],
				delivery_option=data['delivery_option'],
				created_on=data['time_of_order'],
			)
			order.save()

			if data['delivery_option'] == 'delivery':
				# create a shipping address and attach to order
				#  or use the customer's default address
				pass
			elif data['delivery_option'] == 'pickup':
				order.pickup_time = data['pickup_time']

			for item in data['order_items']:
				order_item = OrderItem(
					item = branch.menu.get(slug=item['item']),
					quantity = item['quantity'],
				)
				order_item.save()

				customizations = item.get('customizations', None)
				if customizations:
					for customization in customizations:
						option = OrderOption.objects.get(name=customization['option'], food_item=order_item.item)
						choice = CustomOptionChoice.objects.get(customization=option, name=customization['choice'])
						customize = OrderCustomization(
							customization = option,
							choice = choice
						)
						customize.save()
						order_item.customizations.add(customize,)
						order_item.save()
				order.items.add(order_item,)
			order.save()

			customer.orders.add(order,)
			place.orders.add(order,)
			place.save()
			customer.save()
			return Response({'error': None, 'order': OrderSerializer(order, context={'request': request}).data}, status=201)
		except Exception as error:
			print("ERROR:", error)
			return Response({'error': True, 'message': str(error)}, status=500)


class OrderDetailView(APIView):

	@required_params('place')
	def get(self, request, order_id):
		place = request.place
		try:
			order = place.orders.get(order_id=order_id)
			data = {
				'error': None,
				'order': OrderSerializer(order, context={'request': request}).data
			}
			return Response(data)
		except Exception as error:
			data = {'error': True, 'message': str(error)}
			return Response(data, 500)
	
	@required_params('place')
	def post(self, request, order_id):
		place = request.place
		try:
			order:Order = place.orders.get(order_id=order_id)
			action = request.data['action'] or None

			if action and action == 'change-order-status':
				order.status = request.data['status']
				order.save()
			elif action and action == 'change-payment-status':
				print('changing payment status')
				order.payment_status = True
				order.save()
			
			data = {
				'error': None,
				'order': OrderSerializer(order, context={'request': request}).data
			}
			return Response(data)
		except Exception as error:
			data = {'error': True, 'message': str(error)}
			return Response(data, 500)



class ListOrdersView(ListAPIView):
	
	@required_params('place')
	def delete(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		for item in request.data['items']:
			order = place.orders.get(id=item)
			order.delete()
		return Response({'error': False, 'message': "Successfully deleted order"})
	
	@required_params('place')
	def get(self, request):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		all_orders = place.orders.all().order_by('-id')
		orders = OrderSerializer(all_orders, many=True, context={'request': request}).data
		data = {
			'error': None,
			'orders': orders
		}
		return Response(data)



# Customers Handlers
class ListCustomersView(ListAPIView):
	serializer_class = CustomerSerializer
	model = Customer

	def get_queryset(self, request, **kwargs):
		place = Restaurant.objects.get(slug=request.GET.get('place'))
		return place.customers.all()

	def get(self, request, **kwargs):
		try:
			customers = self.get_queryset(request)
			data = self.serializer_class(customers, many=True).data
			print("DATA:", data)
			return Response({ 'error': False, 'data': data})
		except Exception as e:
			return Response({ 'error' : True, 'message': str(e)})


class CreateCustomerView(APIView):

	@required_params('place')
	def post(self, request, **kwargs):
		user = None
		new_customer = None
		place: Restaurant = request.place

		try:
			# create this model method to add an account
			# with an unsable password and return the user instance
			user = User.create_without_password(request.data)
			new_customer = Customer(
				user=user,
				phone=request.data['phone']
			)
			new_customer.save()
			place.customers.add(new_customer,)
			place.save()
			return Response({ 'error': False, 'data': CustomerSerializer(new_customer).data}, 201)
		except Exception as error:
			if user and user.id:
				user.delete()
			if new_customer and new_customer.id:
				new_customer.delete()
			print("Error:", error)
			return Response({ 'error': True, 'message': str(error)}, 500)



# Staff Handlers
class ListStaffView(ListAPIView):
	authentication_classes = [TokenAuthentication,]

	# @login_required('rdr_login')
	@required_params('place')
	def get(self, request):
		place = request.place
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
			'customer',
		])
		roles = [
			{'role': 'admin', 'label': 'Admin'},
			{'role': 'site-manager', 'label': 'Site Manager'},
			{'role': 'customer-response', 'label': 'Customer Response'}
		]

		data = {
			'error': False,
			'roles': roles,
			'permissions': PermissionSerializer(perms, many=True).data
		}
		return Response(data)

	def post(self, request):
		try:
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


class StaffDetailView(APIView):

	@required_params('place')
	def get(self, request, staff_id):
		place: Restaurant = request.place

		try:
			staff = place.staff.get(staff_id=staff_id)
			data = StaffSerializer(staff).data
			return Response({ 'error': False, 'staff': data}, 200)
		except Exception as error:
			print("Error:", error)
			return Response({ 'error': True, 'message': str(error)}, 500)

	@required_params('place')
	def post(self, request, staff_id):
		return Response()


# Restaurant Branch Handlers
class ListBranchesView(APIView):
	
	@required_params('place')
	def get(self, request, **kwargs):
		place:Restaurant = request.place
		branches = place.branches.all()
		data = {
			'branches': BranchSerializer(branches, many=True).data,
		}
		return Response(data=data, status=200)

	@required_params('place')
	def post(self, request, **kwargs):
		# Do permission logic here
		# optimize view by adding permission logic
		# as decorator after `required_params`
		has_perm = True
		data = request.data
		print("DELETE BRANCH DATA:", data)
		if data['action'] == 'remove':
			if has_perm:
				branch = request.place.branches.get(branch_id=data['branch'])
				branch.delete()
				return Response(data={'error': False, 'message':  "Successfully deleted branch"}, status=200)
		else:
			return Response({'error': True, 'message': "Insufficient Permissions", 'verbose': ""})

	@required_params('place')
	def delete(self, request, **kwargs):
		# Do permission logic here
		# optimize view by adding permission logic
		# as decorator after `required_params`
		has_perm = True
		data = request.POST
		if has_perm:
			branch = request.place.branches.get(branch_id=data['branch'])
			branch.delete()
			return Response(data={'error': False, 'message':  "Successfully deleted branch"}, status=200)
		else:
			return Response({'error': True, 'message': "Insufficient Permissions", 'verbose': ""})


class CreateBranchView(APIView):
	allowed_methods = ['GET', 'POST', 'HEAD', 'OPTIONS']

	@required_params('place')
	def get(self, request):
		branch_create_limit = 3
		place:Restaurant = request.place
		branches = place.branches.all()
		
		data = {
			'error': False,
			'branch_quota': branch_create_limit - branches.count(),
			'branches': BranchSerializer(branches, many=True).data,
		}
		return Response(data, 200)

	@required_params('place')
	def post(self, request, **kwargs):
		try:
			place:Restaurant = request.place
			data = request.data

			location = Location(
				country=data['country'],
				state=data['state'],
				city=data['city'],
			)
			location.save()
			currency = Currency.objects.get(code=data['currency'])

			branch = RestaurantBranch(
				place_id=place,
				branch_name = data['branch_name'],
			)
			branch.offer_delivery = data['offer_delivery'] or False
			branch.offer_pickup = data['offer_pickup'] or False
			branch.offer_dine_in = data['offer_dine_in'] or False
			branch.currency = currency
			branch.location = location

			if data['inherit_menu']:
				branch.inherit_menu = True
				branch.inherit_source = place.branches.get(branch_id=data['inherit_source'])
			branch.save()

			place.branches.add(branch,)
			place.save()
			data = {
				'error': False,
				'branch': BranchSerializer(branch).data,
				'message': 'Successfully created new branch'
			}
			return Response(data, 200)
		except Exception as error:
			print("Error:", error)
			return Response({ 'error': True, 'message': str(error)}, 500)


class BranchDetailView(APIView):
	allowed_methods = ['GET', 'POST', 'OPTIONS']

	@required_params('place')
	def get(self, request, branch_id, **kwargs):
		place:Restaurant = request.place
		branch = place.branches.get(branch_id=branch_id)
		data = {
			'error': False,
			'message': "okay",
			'branch': BranchSerializer(branch).data
		}
		return Response(data=data, status=200)

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
	@required_params('place')
	def get(self, request):
		place = request.place
		data = RestaurantSerializer(place, context={'request': request}).data
		return Response({'error': False, 'data': data})

	@required_params('place', 'target', 'object')
	def post(self, request):
		target = request.GET.get('target', None)
		obj = request.GET.get('object', None)
		action = request.data.get('action', None)
		do_action = getattr(self, action)

		try:
			if target == 'restaurant':
				if obj == 'logo':
					do_action(request.place, request.data['logo'])	

			data = {
				'error': False,
				'message': "Operation Successful"				
			}	
			return Response(status=200, data=data)
		except Exception as error:
			return Response({ 'error': True, 'message': str(error)})

	def change_logo(self, place:Restaurant, logo):
		place.logo = logo
		place.save()

	def change_description(self, text):pass


