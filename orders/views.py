from math import floor
from pprint import pprint

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.forms.models import modelformset_factory, model_to_dict
from django.forms.formsets import formset_factory
#from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect

from orders.models import *
from orders.forms import *

#from pandas import pivot_table
#from django_pandas.io import read_frame
from random import randint
from datetime import date, timedelta
from collections import defaultdict

# Utility methods
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DAYS = ['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']
DATE_FORMAT = "%Y-%m-%d"


def get_standing_orders_by_product(qs):
	"""
	Get the standing orders pivot table, by products / day-of-the-week
	:param qs: Django QuerySet
	:return: dict
	"""
	pt = qs.to_pivot_table(
		fieldnames=['product__dough_type__name', 'product', 'day_of_week', 'quantity'],
		rows=['product__dough_type__name', 'product'],
		cols=['day_of_week'],
		values='quantity',
		aggfunc=sum
	).fillna(0.0).astype(int)
	# defaultdict coz we don't know what the keys are ahead of time
	sot = defaultdict(lambda: defaultdict(list))
	for k, p in zip(pt.index.get_values(), pt.fillna(0.0).astype(int).get_values()):
		sot[k[0]][k[1]] = p
	return dict((k, dict(d)) for k, d in sot.iteritems()) # Convert to a dict

def get_standing_orders_by_client(qs):
	"""
	Get the standing orders pivot table, by clients / day-of-the-week
	:param qs: Django QuerySet
	:return: List of tuples with the first column being a Client, 2nd being standing orders for that client for a week
	"""
	pt = qs.to_pivot_table(
		fieldnames=['client', 'day_of_week', 'quantity'],
		rows=['client'],
		cols=['day_of_week'],
		values='quantity',
		aggfunc=sum
	).fillna(0.0).astype(int)
	clients = [Client.objects.get(name=name) for name in pt.index.get_values()]
	return zip(clients, pt.fillna(0.0).astype(int).get_values())

def get_standing_orders(kwargs):
	""" Makes sure all combinations of standing orders exist for the given client, bake, products combinations.
	:return: List(Dict) of data suitable for use in an inline formset
	"""
	client, bake, products = get_bake_details(kwargs)
	data = []
	for product in products:
		for d in range(0,7):
			standing_order, created = StandingOrder.objects.get_or_create(day_of_week= d+1, product = product, client =
				client, bake = bake, defaults = {'quantity': 0})
			data.append(model_to_dict(standing_order))
	return data

def get_bake_details(kwargs):
	client = Client.objects.get(pk=kwargs['client_pk'])
	bake = Bake.objects.get(pk=kwargs['pk'])
	products = Product.objects.filter(active=True).order_by('name', 'weight')  # Only active products
	return (client, bake, products)

def pretty(d, indent=0):
	for key, value in d.iteritems():
		print '\t' * indent + str(key)
		if isinstance(value, dict):
			pretty(value, indent+1)
		else:
			print '\t' * (indent+1) + str(value)



# Utility views
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generate_standing_orders(request):
	""" Generate some dumby standing orders data for all the current clients. 
	"""
	for c in Client.objects.filter(active=True):
		for p in Product.objects.all():
			for b in Bake.objects.all():
				for d in range(1, 8):
					StandingOrder(client=c, product=p, bake=b, day_of_week=d, quantity=randint(0, 5)).save()
	return redirect('home')

def generate_orders(request):
	""" Generate actual orders from standing orders. 
		Should happen daily but for the following day as the mix happens a day before 
		the bake.
	"""
	# day we are calculating for...
	bake_date = date.today() + timedelta(days=1) # ... a day ahead.
	for bake in Bake.objects.all():
		for so in StandingOrder.objects.filter(
			client__active = True,
			product__active = True,
			product__dough_type__regular_bake = True,
			bake = bake,
			day_of_week = (bake_date.isoweekday() - 1 + bake.days_till_deliver) % 7 + 1,
			quantity__gt = 0
		):
			Order(
				product = Product(so.product_id),
				client = Client(so.client_id),
				bake = bake,
				quantity = so.quantity,
				delivery_date = bake_date + timedelta(days=bake.days_till_deliver),
				baked_on = bake_date 
			).save()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Generic views
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HomeView(View):
	template_name = "home.html"
	
	def get(self, request, *args, **kwargs):
		qs = StandingOrder.objects.filter(client__active=True, product__active=True)
		sot = get_standing_orders_by_product(qs)
		
		return render(request, self.template_name, {
			'days': DAYS,
			'sot': sot
		}) 


# Bespoke views
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ClientDetailView(DetailView):
	model = Client
	
	def get_context_data(self, **kwargs):
		context = super(ClientDetailView, self).get_context_data(**kwargs)
		context.setdefault('address', None)
		context['address'] = Address.objects.filter(client=context['client'])
		bakes = {}
		for bake in Bake.objects.all():
			qs = StandingOrder.objects.filter(client=context['client']).filter(bake=bake).filter(product__active=True)
			if len(qs) > 0:
				bakes[bake] = get_standing_orders_by_product(qs)
			else:
				bakes[bake] = []
		context['bake_standing_order_tables'] = bakes
		context['days'] = DAYS
		context['bakes'] = Bake.objects.all()
		context['orders_list'] = Order.objects.filter(client=context['client'], baked_on__gte=date.today(), quantity__gt=0)

		return context

class ClientCreateView(CreateView):
	model=Client
	form_class=ClientForm
	template_name="orders/client_form.html"

	def get(self, request, *args, **kwargs):
		"""
		Handles GET requests and instantiates blank versions of the form
		and its inline formsets.
		"""
		self.object = None
		form_class = self.get_form_class()
		form = self.get_form(form_class)
		address_form = ClientAddressFormSet()
		return self.render_to_response(
			self.get_context_data(form=form, address_form=address_form, page_title='New')
		)

	def post(self, request, *args, **kwargs):
		"""
		Handles POST requests, instantiating a form instance and its inline
		formsets with the passed POST variables and then checking them for
		validity.
		"""
		self.object = None
		form_class = self.get_form_class()
		form = self.get_form(form_class)
		address_form = ClientAddressFormSet(self.request.POST)
		if (form.is_valid() and address_form.is_valid()):
			return self.form_valid(form, address_form)
		else:
			return self.form_invalid(form, address_form)

	def form_valid(self, form, address_form):
		"""
		Called if all forms are valid. Creates a Recipe instance along with
		associated Ingredients and Instructions and then redirects to a
		success page.
		"""
		self.object = form.save()
		address_form.instance = self.object
		address_form.save()
		return HttpResponseRedirect(self.get_success_url())

	def form_invalid(self, form, address_form):
		"""
		Called if a form is invalid. Re-renders the context data with the
		data-filled forms and errors.
		"""
		return self.render_to_response(
			self.get_context_data(form=form,
								  address_form=address_form))

class ClientEditView(UpdateView):
	""" see: http://kevindias.com/writing/django-class-based-views-multiple-inline-formsets/ 
	"""
	template_name = "orders/client_form.html"
	model = Client
	form_class = ClientForm
	#success_url = reverse_lazy('client_list')
	
	def get(self, request, *args, **kwargs):
		"""
		Handles GET requests and instantiates blank versions of the form
		and its inline formsets.
		"""
		self.object = Client.objects.get(pk=kwargs['pk'])
		form_class = self.get_form_class()
		form = self.get_form(form_class)
		address_form = ClientAddressFormSet(instance=self.object)   # parent instance! (not address instance)
		return self.render_to_response(
			self.get_context_data(form=form, address_form=address_form, page_title='Edit')
		)

	def post(self, request, *args, **kwargs):
		"""
		Handles POST requests, instantiating a form instance and its inline
		formsets with the passed POST variables and then checking them for
		validity.
		"""
		self.object = Client.objects.get(pk=kwargs['pk'])
		form_class = self.get_form_class()
		form = self.get_form(form_class)
		address_form = ClientAddressFormSet(self.request.POST, instance=self.object)
		if (form.is_valid() and address_form.is_valid()):
			return self.form_valid(form, address_form)
		else:
			return self.form_invalid(form, address_form)

	def form_valid(self, form, address_form):
		"""
		Called if all forms are valid. Creates a Recipe instance along with
		associated Ingredients and Instructions and then redirects to a
		success page.
		"""
		self.object = form.save()
		address_form.instance = self.object
		address_form.save()
		return HttpResponseRedirect(self.get_success_url())

	def form_invalid(self, form, address_form):
		"""
		Called if a form is invalid. Re-renders the context data with the
		data-filled forms and errors.
		"""
		errors1 = form.errors
		errors2 = address_form.errors
		self.something()
		return self.render_to_response(
			self.get_context_data(form=form, address_form=address_form))

class ClientBakeStandingOrdersEditView(UpdateView):
	template_name = "orders/BakeStandingOrdersEditForm.html"

	def get_success_url(self):
		return reverse_lazy('client_details', kwargs={'pk': self.kwargs['client_pk']})

	def get(self, request, *args, **kwargs):
		init = get_standing_orders(kwargs)  # ensure creation of all products for all days.
		client, bake, products = get_bake_details(kwargs)
		qs = StandingOrder.objects.filter(client=client, bake=bake, product=products).order_by('product__name', 'product__weight')
		formset = BakeStandingOrdersInlineFormset(instance=client, queryset=qs)
		#print "query: ", len(qs), " products: ", len(products)
		return render(request, self.template_name, {
			'client': client,
			'bake': bake,
			'days': DAYS,
			'formset': formset,
			'products': products
		})

	def post(self, request, *args, **kwargs):
		client, bake, products = get_bake_details(kwargs)
		formset = BakeStandingOrdersInlineFormset(request.POST, instance=client)
		if formset.is_valid():
			i = 0
			for form in formset:
				standing_order = form.save(commit=False)
				#standing_order.client = client
				standing_order.bake = bake
				standing_order.product = products[int(floor(i / 7))]
				standing_order.day_of_week = i % 7 + 1
				standing_order.save()
				i += 1
			return HttpResponseRedirect(self.get_success_url())
		else:
			print "Errors: ", formset.errors
			return render(request, self.template_name, {
				'client': client,
				'bake': bake,
				'days': DAYS,
				'formset': formset,
				'products': products
			})

class CutSheetView(View):
	template_name = 'orders/cutsheet.html'
	
	def get(self, request, *args, **kwargs):
		if 'day' in kwargs:
			cut_sheet_date = datetime.strptime(kwargs['day'], DATE_FORMAT)
		else:
			cut_sheet_date = date.today() + timedelta(days=1)
		
		
		qs = Order.objects.filter(baked_on=cut_sheet_date)
		if len(qs) > 0:
			pt = qs.to_pivot_table(
				fieldnames=['product__dough_type__name', 'product', 'bake', 'quantity'],
				values='quantity', 
				rows=['product__dough_type__name', 'product'], 
				cols=['bake'], 
				aggfunc=sum
			).fillna(0.0).astype(int)

			# Get teh bake counts, grouped by dough type
			#product_tallys = zip(pt.index.get_values(), pt.get_values(), product_counts)
			product_tallys = defaultdict(lambda: defaultdict(list))
			for k, p in zip(pt.index.get_values(), pt.get_values()):
				product_tallys[k[0]][k[1]] = p
			product_tallys = dict((k, dict(d)) for k, d in product_tallys.iteritems()) # Convert to a dict
		
			# Get the total dough weights
			product_counts = pt.sum(axis=1)
			dough_totals = defaultdict(list)
			for d in Dough.objects.filter(regular_bake=True):
				dough_totals[d.name] = 0
				for p in Product.objects.filter(dough_type=d):
					dough_totals[d.name] += p.weight * product_counts.loc[str(d)][str(p)]
			# Maybe a nicer way of doing it...?
			# dough_series = pt.sum(axis=0,level=0).sum(axis=1)
			# dough_totals = [dough_series.index.get_values(), dough_series.get_values()]
		
			return render(request, self.template_name, {
				'date': cut_sheet_date,
				'bake_list': Bake.objects.all(),
				'product_tallys': product_tallys,
				'dough_totals': dict(dough_totals)
			})
		
		else:
			return render(request, 'orders/no_order.html', {'date': cut_sheet_date})

class PackingSlipsView(View):
	template_name = 'orders/packing_slips.html'
	
	def get(self, request, *args, **kwargs):
		if 'day' in kwargs:
			day = datetime.strptime(kwargs['day'], DATE_FORMAT)
		else:
			day = date.today()
		
		slips  = defaultdict(lambda: defaultdict(list))
		for c in Client.objects.filter(orders__order__delivery_date=day).distinct():
			for b in Bake.objects.all():
				orders = Order.objects.filter(quantity__gt=0, client=c, bake=b, delivery_date=day)
				if len(orders) > 0:
					slips[c][b] = orders
		slips = dict((k, dict(d)) for k, d in slips.iteritems()) # Convert to a dict
		
		return render(request, self.template_name, { 'slips':slips, 'day':day })

class OrdersListView(ListView):
	model = Order
	queryset = Order.objects.filter(baked_on__gte=date.today(), quantity__gt=0).order_by('client', 'product')

class OrderUpdate(UpdateView):
	model = Order
	form_class = OrderForm
	template_name = "orders/object_edit_form.html"
	success_url = reverse_lazy('order_list')

class OrderCreate(CreateView):
	model = Order
	form_class = OrderForm
	template_name = "orders/object_new_form.html"
	success_url = reverse_lazy('order_list')

	def get_context_data(self, **kwargs):
		context = super(OrderCreate, self).get_context_data(**kwargs)
		context['object_name'] = 'Order'
		return context

class OrderDelete(DeleteView):
	model = Order
	template_name = "orders/confirm_delete.html"
	success_url = reverse_lazy('order_list')

class ProductDetailView(DetailView):
	model = Product

	def get_context_data(self, **kwargs):
		context = super(ProductDetailView, self).get_context_data(**kwargs)

		# Add orders
		context['orders_list'] = Order.objects.filter(
			baked_on__gte=date.today(),
			quantity__gt=0,
			product=self.get_object()
		).order_by('client', 'product')

		# Add product specific Standing Orders
		context['days'] = DAYS
		qs = StandingOrder.objects.filter(client__active=True, product=self.get_object())
		if len(qs) > 0:
			context['sot'] = get_standing_orders_by_client(qs)
		else:
			context['sot'] = []

		return context
