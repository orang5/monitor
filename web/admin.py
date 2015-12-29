from django.contrib import admin
#from django import forms
#from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Permission
from permission import *
admin.site.register(Permission)
