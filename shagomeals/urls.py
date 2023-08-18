from django.contrib import admin
from django.contrib.staticfiles.urls import static
from django.urls import path, include
from django.conf import settings
from . import webhooks
from rest_framework.schemas import get_schema_view


urlpatterns = [
    path('api/', include('api.urls', namespace='api')),
    path('superuser/', admin.site.urls),
    path('admin/', include('dashboard.urls', namespace='dashboard')),
    path('webhook/', webhooks.successful_payment_webhook, name="checkout-hook"),
#    path('forest', include('django_forest.urls')),
    path('openapi/', get_schema_view(
        title="Shago Meals",
        description="API for Shago Meals Storefront",
        version="1.0.0",
        urlconf='places.api.urls',
        url="https://shago.online",
    ), name='openapi-schema'),
    path('', include('core.urls', namespace='core')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site_index_header = "Hotspot"
