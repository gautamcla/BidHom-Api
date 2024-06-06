# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.network.views import *

urlpatterns = [
    path("admin-active-domain/", AdminActiveDomainApiView.as_view()),
    path("admin-active-network-agent/", AdminActiveNetworkAgentApiView.as_view()),
]
