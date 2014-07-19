from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
#from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory

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

def get_standing_orderes_table(qs):
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
			client__active=True, 
			product__active=True,
			product__dough_type__regular_bake=True,
			bake=bake,
			day_of_week=(bake_date.isoweekday() - 1 + bake.days_till_deliver) % 7 + 1
		):
			Order(
				product=Product(so.product_id),
				client=Client(so.client_id),
				bake=bake,
				quantity=so.quantity,
				delivery_date = bake_date + timedelta(days=bake.days_till_deliver),
				baked_on = bake_date 
			).save()



# Generic views
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HomeView(View):
	template_name = "home.html"
	
	def get(self, request, *args, **kwargs):
		qs = StandingOrder.objects.filter(client__active=True, product__active=True)
		sot = get_standing_orderes_table(qs)
		
		return render(request, self.template_name, {
			'days': DAYS,
			'sot': sot
		}) 


# Bespoke views
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ClientDetailView(DetailView):
	model=Client
	
	def get_context_data(self, **kwargs):
		context = super(ClientDetailView, self).get_context_data(**kwargs)
		bakes = {}
		for bake in Bake.objects.all():
			qs = StandingOrder.objects.filter(client=Client.objects.get(pk=self.kwargs['pk'])).filter(bake=bake)
			bakes[bake] = get_standing_orderes_table(qs)
		context['bake_standing_order_tables'] = bakes
		context['days'] = DAYS
		context['bakes'] = Bake.objects.all()
		
		return context

class ClientFormView(UpdateView):
	""" see: http://kevindias.com/writing/django-class-based-views-multiple-inline-formsets/ 
	"""
	template_name = "orders/client_form.html"
	model = Client
	form_class = ClientForm
	success_url = reverse_lazy('client_list')
	
	def get(self, request, *args, **kwargs):
		"""
		Handles GET requests and instantiates blank versions of the form
		and its inline formsets.
		"""
		if 'pk' in kwargs:
			self.object = get_object_or_404(Client, pk=kwargs['pk'])
			address_instance = Address.objects.get(client=self.object)
		else:	
			self.object = None
			
		form = self.get_form(self.get_form_class())
		address_form = ClientAddressFormSet()
		return self.render_to_response(
			self.get_context_data(form=form, formset=address_form)
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
			self.get_context_data(form=form, address_form=address_form)
		)


class ClientStandingOrdersEditView(View):
	template_name = "orders/StandingOrdersEditForm.html"
	
	def get(self, request, *args, **kwargs):
		client = Client.objects.get(pk=kwargs['pk'])
		products = Product.objects.filter(active=True).order_by('name')
		bake_formsets = {}
		for bake in Bake.objects.all():
			
			StandingOrdersFormSet = modelformset_factory(Order, form=OrderFormlet, extra=0, can_order=False, can_delete=False)
			qs = StandingOrder.objects.filter(client=client).filter(bake=bake).filter(product=products)
			pt = qs.to_pivot_table(
				fieldnames=['product', 'day_of_week', 'quantity'],
				rows=['product'], 
				cols=['day_of_week'], 
				values='quantity', 
				aggfunc=sum	
			).fillna(0.0).astype(int)
			init_data = []
			print bake, pt
			qantities = pt.get_values()
			for i, p in enumerate(products):
				for d in range(1, 8):  # Days of the week
					init_data.append({'product': p, 'quantity': qantities[i][d-1], 'client': client, 'day_of_week': d, 'bake': bake})
			#print len(init_data), init_data[0]
			bake_formsets[bake] = StandingOrdersFormSet(initial=init_data)
			
		return render(request, self.template_name, {
			'client': client,
			'bakes': Bake.objects.all(),
			'days': DAYS,
			'bake_formsets': bake_formsets,
			'products': products
		})

class DeactivateView(UpdateView):
	""" Set the 'active' column to false. 
		Policy is that we never delete a client or prooduct as it will mess with the 
		bookkeeping so we deactive instead.
	"""
	# TODO: finish this class
	pass


class ClientDeactivateView(DeactivateView):
	model=Client
	template_name='orders/confirm_delete.html'
	success_url = reverse_lazy('client_list')


class ProductDeactivateView(DeactivateView):
	model=Product
	template_name='orders/confirm_delete.html'
	success_url = reverse_lazy('product_list')


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





