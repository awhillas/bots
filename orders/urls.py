from django.conf.urls import patterns, url
from orders.views import *

urlpatterns = patterns('',
	url(r'^clients/$',                  ListView.as_view(model=Client),	name='client_list'),
	url(r'client/new/$',                ClientCreateView.as_view(),		name='client_new'),
	url(r'client/(?P<pk>\d+)/$',        ClientDetailView.as_view(),		name='client_details'),
	url(r'client/(?P<pk>\d+)/edit/$',   ClientEditView.as_view(),		name='client_edit'),
	url(r'client/(?P<client_pk>\d+)/standingorders/(?P<pk>\d+)/edit', ClientBakeStandingOrdersEditView.as_view(), name='client_bake_edit'),

	url(r'^products/$',                 ListView.as_view(model=Product),name='product_list'),
	url(r'product/new/$',               CreateView.as_view(model=Product, form_class=ProductForm, template_name="orders/object_new_form.html"),	name='product_new'),
	url(r'product/(?P<pk>\d+)/$',       ProductDetailView.as_view(),	name='product_details'),
	url(r'product/(?P<pk>\d+)/edit/$',  UpdateView.as_view(model=Product, form_class=ProductForm, template_name="orders/object_edit_form.html"), name='product_edit'),

	url(r'^orders/$',					OrdersListView.as_view(),	name='order_list'),
	url(r'^order/new/$',				OrderCreate.as_view(),		name='order_new'),
	url(r'^order/(?P<pk>\d+)/edit/$',	OrderUpdate.as_view(),		name='order_edit'),
	url(r'^order/(?P<pk>\d+)/delete/$',OrderDelete.as_view(),		name='order_delete'),

	url(r'^gen_so/$',	generate_standing_orders,	name='gen_standing_orders'),
	url(r'^so2orders/$',generate_orders,			name='standing_orders_to_orders'),

	url(r'^cutsheet/$',                 CutSheetView.as_view(), name='cut_sheet'),
	url(r'^cutsheet/(?P<day>[\d-]+)/$', CutSheetView.as_view(), name='cut_sheet'),

	url(r'^packingslips/$',                 PackingSlipsView.as_view(), name='packing_slips'),
	url(r'^packingslips/(?P<day>[\d-]+)/$', PackingSlipsView.as_view(), name='packing_slips'),
)


