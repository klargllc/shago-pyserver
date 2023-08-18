from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse



@csrf_exempt
def successful_payment_webhook(request):
	
	return HttpResponse(status=200)