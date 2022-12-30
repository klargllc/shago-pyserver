import os
from random import randint, choice



def generate_staff_id():
	char = os.urandom(4).hex()
	return char


def generate_invoice_id():
	char = os.urandom(4).hex()
	return char.upper()


def parse_image_url(image):
	return 'http://localhost:8000' + image.image.url


def get_average_rating(reviews):
	_1_stars = 0; _2_stars = 0; _3_stars = 0; _4_stars = 0; _5_stars = 0
	for review in reviews:
		if review.rating == 1:
			_1_stars += 1
		elif review.rating == 2:
			_2_stars += 1
		elif review.rating == 3:
			_3_stars += 1
		elif review.rating == 4:
			_4_stars += 1
		elif review.rating == 5:
			_5_stars += 1
	score = (
		(_1_stars * 1) + 
		(_2_stars * 2) + 
		(_3_stars * 3) + 
		(_4_stars * 4) + 
		(_5_stars * 5)
		)
	res = (
		_5_stars +
		_4_stars +
		_3_stars +
		_2_stars +
		_1_stars
		)
	if not res == 0:
		ans = round(float(score / res), 1)
		return str(ans)
	return "0.0"


def slugify(string):
	string = string.lower().replace(' ', '-').replace("'", '')
	string = string.replace('.', '')
	return string


