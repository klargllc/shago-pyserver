from django.db import models


class Review(models.Model):
	author = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
	rating = models.IntegerField()
	comment = models.CharField(max_length=500, blank=True, null=True)
	place_id = models.ForeignKey('places.Restaurant', on_delete=models.CASCADE)

	def reviewer_name(self):
		return self.author.get_full_name()

	def __str__(self):
		return self.author.first_name + ' review'



class SearchMetric(models.Model):
	query = models.CharField(max_length=250)
	person = models.ForeignKey("accounts.Customer", blank=True, null=True, on_delete=models.CASCADE)
	place_id = models.ForeignKey("places.Restaurant", blank=True, null=True, on_delete=models.CASCADE)
	results = models.ManyToManyField("places.FoodItem", blank=True)
	incidents = models.IntegerField(default=0)

	def __str__(self):
		return self.query



class FoodMetric(models.Model):
	EVENTS = (
		('sale', 'sale'),
		('view', 'view'),
		('carting', 'carting'),
		('wishlist', 'wishlist'),
	)
	date = models.DateTimeField(auto_now=True)
	event_type = models.CharField(max_length=100, choices=EVENTS)
	person = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE)

