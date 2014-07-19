from django.conf.urls import patterns, url
from orders.views import *

urlpatterns = patterns('',
	url(r'^clients/$', ListView.as_view(model=Client), name='client_list'),
	url(r'client/(?P<pk>\d+)/$', ClientDetailView.as_view(model=Client), name='client_details'),
	url(r'client/new/$', CreateView.as_view(model=Client, form_class=ClientForm, template_name="orders/new_form.html"), name='client_new'),
	#url(r'client/edit/(?P<pk>\d+)/$', UpdateView.as_view(model=Client, form_class=ClientForm, template_name="orders/new_form.html"), name='client_edit'),
	url(r'client/edit/(?P<pk>\d+)/$', ClientFormView.as_view(), name='client_edit'),
	url(r'client/edit/(?P<pk>\d+)/standingorders/$', ClientStandingOrdersEditView.as_view(), name='client_edit_standingorders'),
	url(r'client/deactivate/(?P<pk>\d+)/$', ClientDeactivateView.as_view( success_url = reverse_lazy('client_list') ), name='client_deactivate'),

	url(r'^products/$', ListView.as_view(model=Product), name='product_list'),
	url(r'product/(?P<pk>\d+)/$', DetailView.as_view(model=Product), name='product_details'),
	url(r'product/new/$', CreateView.as_view(model=Product, form_class=ProductForm, template_name="orders/new_form.html"), name='product_new'),
	url(r'product/edit/(?P<pk>\d+)/$', UpdateView.as_view( model=Product, form_class=ProductForm, template_name="orders/new_form.html" ), name='product_edit'),
	url(r'product/deactivate/(?P<pk>\d+)/$', ProductDeactivateView.as_view(success_url=reverse_lazy('product_deactivate')), name='product_deactivate'),

	url(r'^orders/$', ListView.as_view(model=Order), name='order_list'),
	url(r'^gen_so/$', generate_standing_orders, name='gen_standing_orders'),	
	url(r'^so2orders/$', generate_orders, name='standing_orders_to_orders'),
	
	url(r'^cutsheet/$', CutSheetView.as_view(), name='cut_sheet'),
	url(r'^cutsheet/(?P<day>[\d-]+)/$', CutSheetView.as_view(), name='cut_sheet'),
	
	url(r'^packingslips/$', PackingSlipsView.as_view(), name='packing_slips'),
	url(r'^packingslips/(?P<day>[\d-]+)/$', PackingSlipsView.as_view(), name='packing_slips'),
)