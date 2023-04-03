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
	BusinessAccount,
)



class PermissionSerializer(ModelSerializer):
	class Meta:
		model = Permission
		fields = '__all__'


class UserSerializer(ModelSerializer):
	class Meta:
		fields = ('first_name', 'last_name', 'email',)
		model = Account


class BusinessAccountSerializer(ModelSerializer):
	user = UserSerializer()
	store = StringRelatedField()
	class Meta:
		fields = '__all__'
		model = BusinessAccount


class StaffSerializer(ModelSerializer):
	user = UserSerializer()
	place = StringRelatedField()
	class Meta:
		fields = ('id', 'user', 'staff_id', 'permissions', 'place')
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
		fields =('url', 'id')
		model = FoodImage

	def get_url(self, obj):
		req = self.context.get('request')
		url = req.build_absolute_uri(obj.image.url)
		return url


class CustomizationOptionSerializer(ModelSerializer):
	class Meta:
		fields = ('option', 'price')
		model = CustomizationOption


class CustomizationSerializer(ModelSerializer):
	options = CustomizationOptionSerializer(many=True)
	default_option = CustomizationOptionSerializer()
	class Meta:
		fields = ('id', 'title', 'options', 'required', 'default_option')
		model = Customization


class FoodSerializer(ModelSerializer):
	images = FoodImageSerializer(many=True)
	image = FoodImageSerializer()
	customizations = CustomizationSerializer(many=True)
	category = StringRelatedField()
	
	class Meta:
		fields = (
			'id', 'name', 'about', 'slug',
			'price', 'image', 'tags', 'images', 
			'category', 'customizations', 'rating',
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
		fields = ('id', 'invoice', 'created_on', 'items', 'customer', 'status', 'delivery_is_on', 'subtotal')
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


class RestaurantSerializer(ModelSerializer):
	owner = BusinessAccountSerializer()
	class Meta:
		model = Restaurant
		fields = (
			'about', 'banner', 'name',
			'slug', 'logo', 'links',
			'owner', 'categories', 'reviews'
			)