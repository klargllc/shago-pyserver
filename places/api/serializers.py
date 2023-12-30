from rest_framework.serializers import (
	ModelSerializer,
	StringRelatedField,
	HyperlinkedRelatedField,
	SerializerMethodField,
	SlugRelatedField,
)
from ..models import *
from accounts.models import(
	Account,
	Customer,
	RestaurantStaff,
	Merchant,
	RestaurantStaffRole
)


class CurrencySerializer(ModelSerializer):
	class Meta:
		model = Currency
		fields = ('code', 'symbol', 'country', 'id')

class PermissionSerializer(ModelSerializer):
	class Meta:
		model = Permission
		fields = '__all__'


class StaffRoleSerializer(ModelSerializer):
	class Meta:
		model = RestaurantStaffRole
		fields = '__all__'

class UserSerializer(ModelSerializer):
	class Meta:
		fields = ('first_name', 'last_name', 'email',)
		model = Account


class MerchantSerializer(ModelSerializer):
	user = UserSerializer()
	store = StringRelatedField()
	class Meta:
		fields = '__all__'
		model = Merchant


class StaffSerializer(ModelSerializer):
	user = UserSerializer()
	place = StringRelatedField()
	branch_id = StringRelatedField()
	role = StringRelatedField()
	class Meta:
		fields = ('id', 'user', 'staff_id', 'role', 'place', 'branch_id')
		model = RestaurantStaff



class CategorySerializer(ModelSerializer):
	class Meta:
		model = Category
		fields = ('id', 'name', 'item_count')


class TagSerializer(ModelSerializer):
	class Meta:
		model = Tag
		fields = ('id', 'tag')


class CustomerSerializer(ModelSerializer):
	user = UserSerializer()
	class Meta:
		fields = ('id', 'user', 'phone', 'orders')
		model = Customer


class FoodImageSerializer(ModelSerializer):
	url = SerializerMethodField()
	
	class Meta:
		fields = ('url', 'id')
		model = FoodImage

	def get_url(self, obj):
		req = self.context.get('request')
		url = req.build_absolute_uri(obj.image.url)
		return url


class CustomOptionChoiceSerializer(ModelSerializer):
	class Meta:
		fields = ('name', 'price')
		model = CustomOptionChoice


class OrderOptionSerializer(ModelSerializer):
	choices = CustomOptionChoiceSerializer(many=True)
	default_choice = CustomOptionChoiceSerializer()
	class Meta:
		fields = ('id', 'name', 'choices', 'required', 'default_choice')
		model = OrderOption


class FoodSerializer(ModelSerializer):
	images = FoodImageSerializer(many=True)
	image = FoodImageSerializer()
	custom_choices = OrderOptionSerializer(many=True)
	category = StringRelatedField()
	
	class Meta:
		fields = (
			'id', 'name', 'about', 'slug',
			'price', 'image', 'tags', 'images', 
			'category', 'custom_choices', 'rating',
		)
		model = FoodItem


class OrderItemSerializer(ModelSerializer):
	item = FoodSerializer()

	class Meta:
		fields = ('item', 'id', 'quantity', 'total')
		model = OrderItem


class CartSerializer(ModelSerializer):
    items = OrderItemSerializer(many=True)
    owner = StringRelatedField()
    restaurant = StringRelatedField()

    class Meta:
        model = BuyerCart
        fields = '__all__'



class OrderSerializer(ModelSerializer):
	items = OrderItemSerializer(many=True)
	customer = CustomerSerializer()

	class Meta:
		fields = ('id', 'order_id', 'invoice', 'created_on', 'items', 'customer', 'status', 'delivery_option', 'subtotal', 'payment_status')
		model = Order


class ReviewSerializer(ModelSerializer):
	food = StringRelatedField()
	reviewer = StringRelatedField()
	class Meta:
		model = 'metrics.Review'
		fields = ('id', 'reviewer', 'rating', 'comment')


class NotificationSerializer(ModelSerializer):
	class Meta:
		model = 'accounts.UserNotification'
		fields = ('id', 'type', 'text')



class BranchSerializer(ModelSerializer):
	currency = StringRelatedField()
	class Meta:
		model = RestaurantBranch
		fields = '__all__'

class RestaurantSerializer(ModelSerializer):
	owner = MerchantSerializer()
	branches = BranchSerializer(many=True)
	logo_url = SerializerMethodField()
	class Meta:
		model = Restaurant
		fields = (
			'about', 'banner', 'name',
			'slug', 'logo_url', 'links',
			'owner', 'categories', 'reviews',
			'branches', 'main_branch'
		)
	
	def get_logo_url(self, obj):
		if obj.logo:
			request = self.context.get('request')
			if request:
				return request.build_absolute_uri(obj.logo.url)
		return ""


