from django.utils.deprecation import MiddlewareMixin
from .models import UserProfile, Merchant, Customer, RestaurantStaff as Staff
from rest_framework.authtoken.models import Token
from rest_framework.request import HttpRequest

class TokenAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request:HttpRequest, **kwargs):
        try:
            token:str = request.headers['Authorization']
            if token:
                token = token.split(' ')[1]
                user = Token.objects.get(key=token).user
                request.user = user
        except Exception as e:
            pass

class ProfileMiddleware(MiddlewareMixin):
    def process_request(self, request:HttpRequest, **kwargs):
        profile = None
        if request.user.is_authenticated:
            try:
                profile = Merchant.objects.get(user=request.user)
            except Exception:
                try:
                    profile = Customer.objects.get(user=request.user)
                except Exception:
                    try:
                        profile = Staff.objects.get(user=request.user)
                    except Exception as e:
                        # proprietary users
                        pass
        request.profile = profile


