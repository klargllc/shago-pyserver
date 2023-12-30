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
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            for param in params:
                if param not in request.GET:
                    print(f"Missing Params: {param}")
                    return Response({"error": f"Missing required parameter: {param}"}, status=400)
                print(f"Good to go on param: {param}")
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator