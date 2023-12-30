from django.contrib import admin
from django.contrib.staticfiles.urls import static
from django.urls import path, include
from django.conf import settings
from . import webhooks


urlpatterns = [
    path('', include('places.urls', namespace='core')),
    path('api/', include('api.urls', namespace='api')),
    path('superuser/', admin.site.urls),
    path('webhook/', webhooks.successful_payment_webhook, name="checkout-hook"),
    # path('forest', include('django_forest.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site_index_header = "Hotspot"
