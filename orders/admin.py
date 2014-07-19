from django.contrib import admin
from orders.models import *

class AddressInline(admin.StackedInline):
	model = Address
	extra = 1

class ClientAdmin(admin.ModelAdmin):
	inlines = [AddressInline,]

class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'weight', 'sliced', 'category', 'price', 'active', )

class OrderAdmin(admin.ModelAdmin):
	list_display = ('client', 'product', 'quantity',)

admin.site.register(Client, ClientAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Dough)
