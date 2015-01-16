from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory, BaseFormSet

from orders.models import *

class AddressForm(ModelForm):
	class Meta:
		model = Address
		fields = ['address1', 'address2', 'suburb', 'postcode', 'state']

class ClientForm(ModelForm):
	class Meta:
		model = Client
		fields = ['name', 'primary_phone', 'accounts_phone', 'notes', 'active']

ClientAddressFormSet = inlineformset_factory(Client, Address, form=AddressForm, extra=1)

class ProductForm(ModelForm):
	class Meta:
		model = Product
		exclude = []

class StandingOrderFormlet(ModelForm):
	class Meta:
		model = StandingOrder
		fields = ['quantity']
		labels = {'quantity':''}

BakeStandingOrdersInlineFormset = inlineformset_factory(Client, StandingOrder, form=StandingOrderFormlet,
                                                        can_delete=False, extra=0)
