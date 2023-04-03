from django.contrib.auth.models import (
	AbstractBaseUser,
	BaseUserManager,
	Group
)
from django.db import models
from places.utils.helpers import (
	generate_staff_id,
	slugify,
)
from decimal import Decimal



class AccountManager(BaseUserManager):
	def create_superuser(self, email, password=None, **kwargs):
		user = self.create_user(
			email=email,
			password=password,
			is_staff = True,
			is_superuser = True,
			**kwargs
		)
		return user

	def create_user(self, email, password=None, **kwargs):
		user = self.model(
			email=email,
			**kwargs
		)
		if password:
			user.set_password(password)
		else:
			user.set_unusable_password()
		user.save()
		return user


class Account(AbstractBaseUser):
	first_name = models.CharField(max_length=150, blank=True, null=True)
	last_name = models.CharField(max_length=150, blank=True, null=True)
	role = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)
	email = models.EmailField(unique=True)

	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)

	date_joined = models.DateTimeField(auto_now=True)
	last_login = models.DateTimeField(blank=True, null=True)

	objects = AccountManager()
	REQUIRED_FIELDS = ['first_name']
	USERNAME_FIELD = 'email'

	@property
	def name(self):
		return f'{self.first_name} {self.last_name}'

	def has_module_perms(self, perms):
		return True

	def has_perms(self, perms):
		return True

	def has_perm(self, perm):
		return True


class UserProfile(models.Model):
	user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
	verified_email = models.BooleanField(default=False)
	phone = models.CharField(max_length=20, blank=True, null=True, unique=True)

	class Meta:
		abstract = True

	@property
	def name(self):
	    return self.user.name


class BusinessAccount(UserProfile):
	store = models.OneToOneField("places.Restaurant", blank=True, null=True, on_delete=models.SET_NULL)
	billing_method = models.ForeignKey("BillingMethod", blank=True, null=True, on_delete=models.SET_NULL)

	def __str__(self):
		return self.user.name


class RestaurantStaff(UserProfile):
	place = models.ForeignKey("places.Restaurant", on_delete=models.CASCADE, related_name='org')
	staff_id = models.CharField(default=generate_staff_id, max_length=20)

	@property
	def permissions(self):
		return self.user.permissions.all()

	def grant_permission(self, perm):
		return

	def revoke_permission(self, perm):
		return


class BillingMethod(models.Model):
	owner = models.OneToOneField("places.Restaurant", on_delete=models.CASCADE)
	name_on_card = models.CharField(max_length=200)
	address = models.CharField(max_length=500)
	card_number = models.CharField(max_length=16)
	exp_month = models.IntegerField()
	exp_year = models.IntegerField()
	cvc = models.CharField(max_length=3)

	def __str__(self):
		return self.name_on_card


# withdrawal
class PaymentInformation(models.Model):
	place = models.OneToOneField('places.Restaurant', on_delete=models.CASCADE)
	bank_name = models.CharField(max_length=150)
	account_name = models.CharField(max_length=150)
	account_number = models.CharField(max_length=150)
	bank_code = models.CharField(max_length=150)


class ShippingAddress(models.Model):
	owner = models.ForeignKey("Customer", on_delete=models.CASCADE)
	country = models.CharField(default='Nigeria', max_length=100)
	state = models.CharField(default='Kaduna', max_length=100)
	city = models.CharField(default='Kaduna', max_length=100)
	address = models.CharField(max_length=400)
	zip_code = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f'{self.owner.user.get_full_name()} - {self.address}'


class Customer(UserProfile):
	carts = models.ManyToManyField("places.BuyerCart", blank=True)
	orders = models.ManyToManyField("places.Order", blank=True, related_name='orders')

	def __str__(self):
		return self.user.name

	class Meta:
		abstract = False

	def joined(self):
		return self.user.date_joined


class UserNotification(models.Model):
	user = models.ForeignKey("Customer", on_delete=models.CASCADE)
	priority = models.CharField(max_length=20)
	message = models.TextField()
	created = models.DateTimeField(auto_now=True)


	def __str__(self):
		pass


class Integration(models.Model):
	service = models.CharField(max_length=100, blank=True, null=True)
	token = models.CharField(max_length=70, blank=True, null=True)
	webhook_endpoint = models.URLField(blank=True, null=True)
	related_place = models.ForeignKey("places.Restaurant", on_delete=models.CASCADE)
	permission = models.BooleanField(default=False)
	date_approved = models.DateField(blank=True, null=True)
	instance_id = models.CharField(max_length=200, unique=True)
	app_id = models.CharField(max_length=200, unique=True) # unique identifier


	def __str__(self):
		return self.service



# Base settings for any restaurant
# class SiteSettings(models.Model):
# 	site = models.OneToOneField('Site', on_delete=models.CASCADE)
# 	# brand_color_palette = models
# 	site_name = pass
# 	custom_url = pass
# 	dns_location = pass # dns url endpoint
