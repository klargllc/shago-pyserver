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
    StaffDetailView,
	ListCustomersView,
	CreateCustomerView,
    CreateBranchView,
    ListBranchesView,
    BranchDetailView,
	ManagerView,
	login_view,
	resource_view,
	search_view,
	ManageCategoriesView,
)

app_name = 'dashboard'

urlpatterns = [
	path('login/', login_view),
	path('find/', search_view),
	path('res/', resource_view),
	path('dashboard/', DashboardView.as_view()),
	path('manage/', ManagerView.as_view()),
	
	path('menu/', ListFoodItemView.as_view()),
	path('menu/add/', CreateFoodItemView.as_view()),
	path('menu/cats/', ManageCategoriesView.as_view()),
	path('menu/<slug>/', EditFoodItemView.as_view()),
    
	path('orders/add/', CreateOrderView.as_view()),
	path('orders/<order_id>/', OrderDetailView.as_view()),
	path('orders/', ListOrdersView.as_view()),
	
	path('staff/add/', CreateStaffView.as_view()),
	path('staff/<staff_id>/', StaffDetailView.as_view()),
	path('staff/roles/', ListStaffView.as_view()),
	path('staff/', ListStaffView.as_view()),

	path('branches/add/', CreateBranchView.as_view()),
	path('branches/<branch_id>/', BranchDetailView.as_view()),
	path('branches/', ListBranchesView.as_view()),
	
	path('customers/', ListCustomersView.as_view()),
	# path('customers/', ListCustomersView.as_view()),
	path('customers/add/', CreateCustomerView.as_view()),

]