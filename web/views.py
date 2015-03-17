from django.shortcuts import render_to_response
from django.contrib import auth
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def index(request):
    return render_to_response('index.html')