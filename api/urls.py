from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt

app_name = 'api'

urlpatterns = [
    # path('v1/', include('places.api.urls', namespace='places_api')),
    path('places/', include('places.api.urls', namespace='places_api')),
    path('dashboard/', include('dashboard.api.urls', namespace='dashboard_api')),
    path('docs/', TemplateView.as_view(
        template_name='docs/swagger-ui-docs.html',
        extra_context={
            'schema_url':'openapi-schema', 
        }
    ), name='docs')
]
 