from django.contrib import admin
from .models import (
	Account,
	Customer,
	BusinessAccount,
	RestaurantStaff,
	ShippingAddress,
	BillingMethod,
	UserNotification,
)



# Register your models here.
admin.site.register(Account)
admin.site.register(Customer)
admin.site.register(BusinessAccount)
admin.site.register(RestaurantStaff)
admin.site.register(ShippingAddress)
admin.site.register(BillingMethod)
admin.site.register(UserNotification)