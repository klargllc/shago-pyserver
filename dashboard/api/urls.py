from django.urls import path
from .views import (
	DashboardView,
	CreateFoodItemView,
	MenuView,
	EditFoodItemView,
	ListOrdersView,
	OrderDetailView,
	CreateOrderView,
	CreateStaffView,
    ChangeStaffView,
	ListStaffView,
	ListCustomersView,
    CreateCustomerView,
	ManagerView,
    ListBranchView,
    ManageBranchView,
    CreateBranchView,
    ListNotificationsView,
	login_view,
	resource_view,
	search_view,
	categories_management_view,
)

app_name = 'dashboard_api'

urlpatterns = [
	path('login/', login_view),
	path('find/', search_view),
	path('res/', resource_view),
	path('manage/', ManagerView.as_view()),
	
	path('notifications/<branchId>/', ManageBranchView.as_view()),
	path('notifications/', ListNotificationsView.as_view()),
    
	path('branches/add/', CreateBranchView.as_view()),
	path('branches/<branchId>/', ManageBranchView.as_view()),
	path('branches/', ListBranchView.as_view()),
    
	path('menu/', MenuView.as_view()),
	path('menu/add/', CreateFoodItemView),
	path('menu/cats/', categories_management_view),
	path('menu/<itemId>/', EditFoodItemView.as_view()),
	
	path('orders/', ListOrdersView.as_view()),
	path('orders/add/', CreateOrderView.as_view()),
	path('orders/<orderId>/', OrderDetailView.as_view()),
    
	path('staff/', ListStaffView.as_view()),
	path('staff/add/', CreateStaffView.as_view()),
	path('staff/<staffId>/', ChangeStaffView.as_view()),
	
	path('customers/', ListCustomersView.as_view()),
	path('customers/add/', CreateCustomerView.as_view()),
	
	path('', DashboardView.as_view()),

]