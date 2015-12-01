from django.conf.urls import patterns, include, url
from django.contrib import admin
from web.views import *

urlpatterns = patterns('',
    url(r'^$', login),
    url(r'^index/$',index),
    url(r'^index_update/$',index_update),
    url(r'^Vplatform/$', vplatform),
    url(r'^Host_static/$', Host_static),
    url(r'^VirtualMachine/$', virtualMachine),
    url(r'^VirtualMachineUpdate/$', virtualMachine_update),
    url(r'^Network/$', network),
    url(r'^Management/$', management),
    url(r'^users/$', usersManager),
    url(r"^BaseUpdate/$", vm_list),
    url(r"^Event/$", eventLog)
)