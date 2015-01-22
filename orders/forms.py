#from django import forms
import floppyforms.__future__ as forms
from django.forms.models import inlineformset_factory

from orders.models import *

class AddressForm(forms.ModelForm):
	class Meta:
		model = Address
		fields = ['address1', 'address2', 'suburb', 'postcode', 'state']

class ClientForm(forms.ModelForm):
	class Meta:
		model = Client
		fields = ['name', 'primary_phone', 'accounts_phone', 'notes', 'active']

ClientAddressFormSet = inlineformset_factory(Client, Address, form=AddressForm, extra=1)

class ProductForm(forms.ModelForm):
	class Meta:
		model = Product
		fields = '__all__'

class StandingOrderFormlet(forms.ModelForm):
	class Meta:
		model = StandingOrder
		fields = ['quantity']
		labels = {'quantity':''}

BakeStandingOrdersInlineFormset = inlineformset_factory(Client, StandingOrder, form=StandingOrderFormlet,
                                                        can_delete=False, extra=0)

class OrderForm(forms.ModelForm):
	class Meta:
		model = Order
		fields = '__all__'
