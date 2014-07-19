from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory

from orders.models import *

class AddressForm(ModelForm):
	class Meta:
		model = Address
		fields = ['address1', 'address2', 'suburb', 'postcode', 'state']

class ClientForm(ModelForm):
	class Meta:
		model = Client
		fields = ['name', 'primary_phone', 'accounts_phone', 'notes']

ClientAddressFormSet = inlineformset_factory(Client, Address, form=AddressForm, extra=1, can_delete=False)

class ProductForm(ModelForm):
	class Meta:
		model = Product

class StandingOrderFormlet(forms.Form):
	""" Form for use in the formset data grid. """
	forms.IntegerField(min_value=0)
	
class OrderFormlet(ModelForm):
	class Meta:
		model = Order
		fields = ['quantity']

OrderFormSet = inlineformset_factory(Client, Order, form=OrderFormlet)
