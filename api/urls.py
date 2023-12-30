from django.urls import path, include


app_name = 'api'


urlpatterns = [
    path('admin/', include('dashboard.urls', namespace='dashboard')),
    path('places/', include('places.api.urls', namespace='places')),
    
]
