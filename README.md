# Brickfields Order Tracking System (BOTS)
by Alexander Whillas <whillas@gmail.com>

Brickfields Order Tracking System, order management for Brickfields bakery.

Order tacking system for standing orders and piece-meal orders.


## Requirements

Python 2.7.9
Django 1.7.2
MySQL 5.6.17


## Setup

These are some of the python modules that need to be setup

You should probably upgrade `pip` befre you start

	pip install -U pip

These install/upgrade the following	

	sudo pip install -U Django
	sudo pip install -U django_pandas
	pip install -U django-floppyforms

Once you have done all of this you should test your instillation that it works with the current version of the web-app

	python -Wall manage.py test
