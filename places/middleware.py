from django.utils.deprecation import MiddlewareMixin
from .models import Restaurant


class PlacesMiddleware(MiddlewareMixin):

	def process_request(self, request, **kwargs):
		placeId = request.GET.get('place', None)
		if placeId:
			request.place = Restaurant.objects.get(slug=placeId)
		else:
			request.place = None

