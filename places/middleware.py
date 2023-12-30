from django.utils.deprecation import MiddlewareMixin
from .models import Restaurant
import logging


logger = logging.Logger('EventLog')

class PlacesMiddleware(MiddlewareMixin):

	def process_request(self, request, **kwargs):
		placeId = request.GET.get('place', None)
		branchId = request.GET.get('branch', None)
		if placeId:
			request.place = Restaurant.objects.get(slug=placeId)
			if branchId:
				request.branch = request.place.branches.get(branch_id=branchId)
			else:
				request.branch = None
		else:
			request.place = None

class VerboseLogMiddleware(MiddlewareMixin):

	def process_request(self, request, **kwargs):
		if request.method == 'POST':
			logger.info("")
		elif request.method == 'DELETE':
			logger.info("")
		else:
			logger.info("")


