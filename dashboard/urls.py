from django.urls import path
from .views import (
	DashboardView,
	CreateFoodItemView,
	ListFoodItemView,
	EditFoodItemView,
	ListOrdersView,
	OrderDetailView,
	CreateOrderView,
	CreateStaffView,
	ListStaffView,
	ListCustomersView,
	ManagerView,
	login_view,
	resource_view,
	search_view,
	categories_management_view,
)

app_name = 'dashboard'

urlpatterns = [
	path('login/', login_view),
	path('find/', search_view),
	path('res/', resource_view),
	path('dashboard/', DashboardView.as_view()),
	path('manage/', ManagerView.as_view()),
	path('menu/', ListFoodItemView.as_view()),
	path('menu/add/', CreateFoodItemView),
	path('menu/cats/', categories_management_view),
	path('menu/<slug>/', EditFoodItemView.as_view()),
	path('orders/', ListOrdersView.as_view()),
	path('orders/add/', CreateOrderView.as_view()),
	path('orders/<invoice>/', OrderDetailView.as_view()),
	path('staff/', ListStaffView.as_view()),
	path('staff/add/', CreateStaffView.as_view()),
	path('customers/', ListCustomersView.as_view()),
	path('customers/add/', CreateStaffView.as_view()),

]