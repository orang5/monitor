from django.conf.urls import patterns, include, url
from django.contrib import admin
from web.views import *

urlpatterns = patterns('',
    url(r'^$',index),
    url(r'^index_update/$',index_update),
    url(r'^VirtualMachine/$', virtualMachine),
    url(r'^VirtualMachineUpdate/$', virtualMachine_update)
)