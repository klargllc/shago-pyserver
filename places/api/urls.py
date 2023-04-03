from django.urls import path
from .views import (
	signup_view,
	login_view,
	place_view,
	menu_view,
	item_detail_view,
	cart_view,
	search_view,
	checkout_view,
	notifications_view,
	leave_a_review,
	user_account_view,
	user_account_orders_view,
	user_account_order_detail_view,
)

app_name = 'api'

urlpatterns = [
	# authentication
	path('login/', login_view),
	path('signup/', signup_view),

	# customer
	path('find/', search_view),
	path('menu/', menu_view),
	path('menu/item/', item_detail_view),
	path('review/', leave_a_review),
	
	path('cart/', cart_view),
	path('checkout/', checkout_view),
	path('me/', user_account_view),
	path('me/orders/', user_account_orders_view),
	path('me/orders/view/', user_account_orders_view),
	path('notifications/', notifications_view),
	path('place/', place_view),
]