# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.home.views import *

urlpatterns = [
    path("detail/", DetailApiView.as_view()),
]
