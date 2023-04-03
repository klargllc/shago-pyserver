from decimal import Decimal
from functools import wraps
from rest_framework.response import Response

def calc_subtotal(items):
	num = 0
	for i in items:
		num += i.total
	return Decimal(num)

def calc_deivery_fee(order):
	return Decimal('7.00')


def calc_vat(order):
	return Decimal('1.23')


def calc_processing_fee(order_total):
	return Decimal('2.03')

# decorators
def required_params(*params):
	def decorator(main_view):
		@wraps(main_view)
		def view_handler(request, *args, **kwargs):
			for param in params:
				if not param in request.GET.keys():
					print("Param missing:", param)
					return Response(status=400, data={'error': f'{param} param missing'})
				else:
					return main_view(request, *args, **kwargs)
		return view_handler
	return decorator

