from django.db import models
from ..utils.helpers import (
	generate_staff_id,
	generate_invoice_id,
	get_average_rating,
	slugify,
	parse_image_url,
)
from rest_framework.authtoken.models import Token
from decimal import Decimal
from .orders import *
from .places import *
