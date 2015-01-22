from datetime import datetime, timedelta
from django.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse

from django_pandas.managers import DataFrameManager

class Address(models.Model):
	""" Australian address field. 
	"""
	client = models.ForeignKey("Client")
	address1 = models.CharField(blank=True, max_length=100)
	address2 = models.CharField(blank=True, max_length=100)
	suburb = models.CharField(blank=True, max_length=100)
	postcode = models.CharField(blank=True, max_length=100)
	state = models.CharField(blank=True, max_length=4, default="NSW")

	class Admin:
		list_display = ('address1', 'postcode', 'state')
		search_fields = ('address1', 'address2', 'suburb', 'postcode', 'state',)

	def __unicode__(self):
		return ', '.join([self.address1, self.address2, self.suburb, self.postcode, self.state])

	def html(self):
		# TODO: Should spit out hCard microformat: http://microformats.org/wiki/hcard
		return '<br>'.join(filter(None, [self.address1, self.address2, self.suburb, self.postcode, self.state]))


class Category(models.Model):
	""" Bread product category.
	"""
	name = models.CharField(blank=True, max_length=100, unique=True)

	class Admin:
		list_display = ('name',)
		search_fields = ('',)

	def __unicode__(self):
		return self.name


class Dough(models.Model):
	""" Dough types. 
	"""
	name = models.CharField(blank=True, max_length=100, unique=True)
	regular_bake = models.BooleanField(default=True)
	
	class Admin:
		list_display = ('name',)
		search_fields = ('',)

	def __unicode__(self):
		return self.name


class Bake(models.Model):
	""" One of the daily bake (events). 
		For grouping orders into baking runs on the cut-sheet.
	"""
	name = models.CharField(blank=False, max_length=50, unique=True,
		help_text="Name that appears on the cut-sheet.")
	ordering = models.PositiveSmallIntegerField(blank=False, null=False,
		help_text="Where in the order of bakes does this bake happen.")
	days_till_deliver = models.PositiveSmallIntegerField(blank=False, null=False,
		help_text="How many days from the bake will the goods be delivered? Zero for same day. 1 for next day.")
	standing_orders = models.ManyToManyField("Client",
		through='StandingOrder', related_name="bake_standing_orders")

	def __unicode__(self):
		return self.name + " Bake"


class Product(models.Model):
	""" Product that is produced by the bakery. 
	"""
	name = models.CharField(blank=False, null=False, max_length=100)
	ingredients = models.TextField(blank=True, null=True)
	category = models.ForeignKey(Category)
	dough_type = models.ForeignKey(Dough, blank=False, null=False)
	weight = models.IntegerField(blank=False, null=False, help_text="grams")
	sliced = models.BooleanField(default=False)
	price = models.DecimalField(max_digits=6, decimal_places=2,
		help_text="Wholesale price.")
	active = models.BooleanField(default=True, 
		help_text="Available or not. We do not delete products as it messes with the old accounting.")
	special = models.BooleanField(default=False, 
		help_text="Only for special one off orders.")
	large_change_qty = models.PositiveSmallIntegerField(blank=True, null=False, default=0,
		help_text="How many will flag a large change notice in the admin.")

	class Meta:
		unique_together = ('name', 'weight')
		ordering = ['name']

	def get_absolute_url(self):
		return reverse('product_details', kwargs={'pk': self.pk})
		
	def __unicode__(self):
		return ', '.join([self.name, str(intcomma(self.weight)) + 'g'])


class Client(models.Model):
	""" A Paying customer. 
	"""
	name = models.CharField(blank=False, max_length=100, unique=True)
	primary_phone = models.CharField(blank=True, max_length=100, 
		help_text="Their main contact.")
	accounts_phone = models.CharField(blank=True, max_length=100)
	notes = models.TextField(blank=True)
	orders = models.ManyToManyField(Product,
		through='Order', related_name="order_clients")
	standing_orders = models.ManyToManyField(Product,
		through='StandingOrder', related_name="standing_order_clients")
	active = models.BooleanField(default=True, help_text="Do we process this clients orders?")
		
	class Admin:
		list_display = ('name', 'primary_phone')
		search_fields = ('name', 'primary_phone')

	def get_absolute_url(self):
		return reverse('client_details', kwargs={'pk': self.pk})

	def __unicode__(self):
		return self.name


class Order(models.Model):
	""" An actual order for a product. 
		Appears on cut-sheet and is billable.
		StandingOrders get converted to Orders periodically based on the Product.lead_time value
	"""
	product = models.ForeignKey(Product)
	client = models.ForeignKey(Client)
	bake = models.ForeignKey(Bake, related_name='+')
	quantity = models.PositiveSmallIntegerField(blank=True, null=True)
	baked_on = models.DateField(default=datetime.today())
	delivery_date = models.DateField(default=datetime.today()+timedelta(days=1))
	
	objects = DataFrameManager()

	class Meta:
		unique_together = ('product', 'client', 'bake', 'delivery_date')
		ordering = ['product__name']
	
	def convert_standing_order(cls, standing_order, date):
		pass
	
	def get_absolute_url(self):
		return reverse('orders_list', kwargs={'pk': self.pk})

	def __unicode__(self):
		return u", ".join([str(self.quantity)+"x", str(self.product), str(self.client), str(self.bake), str(self.delivery_date)])


class StandingOrder(models.Model):
	""" An order that is repeated every week. 
	"""
	product = models.ForeignKey(Product)
	client = models.ForeignKey(Client)
	bake = models.ForeignKey(Bake, related_name='+')
	day_of_week = models.PositiveSmallIntegerField(blank=False, null=False, 
		help_text="Day of the week of the delivery. Week starts Monday.")
	quantity = models.PositiveSmallIntegerField(blank=True, null=True)
	
	objects = DataFrameManager()    # django-pandas module
	
	class Meta:
		unique_together = ('product', 'client', 'bake', 'day_of_week')
		#ordering = ['product__name']

	class Admin:
		list_display = ('',)
		search_fields = ('',)

	def __unicode__(self):
		return ', '.join(str(i) for i in [self.quantity, self.product, self.day_of_week, self.bake, self.client])