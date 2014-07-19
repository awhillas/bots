from django import template
import collections
#from django.db.models.query import QuerySet

register = template.Library()

@register.filter
def index(value, arg):
	if isinstance(value, collections.Iterable) and len(value) > arg - 1:
		return value[arg]
	else:
		return None

@register.filter
def mod(value, arg):
	if isinstance(value, (int, long, float, complex)):
		return value % arg
	else:
		return None
		
@register.filter
def div(value, arg):
	if isinstance(value, (int, long, float, complex)):
		return value / arg
	else:
		return None

@register.filter
def dayi(value, arg):
	""" Custom filter that divides the arg (index) by 7 before looking up in the 
		collection the value. Nothing reusable about this :( 
	"""
	#print "div: ", value, arg
	if isinstance(arg, (int, long, float, complex)) and isinstance(value, collections.Iterable) and len(value) > arg/7 - 1:
		#print value[arg / 7]
		return value[arg / 7]
	else:
		return None
	