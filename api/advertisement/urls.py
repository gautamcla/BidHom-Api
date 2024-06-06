# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.advertisement.views import *

urlpatterns = [
    path("add-advertisement/", AddAdvertisementApiView.as_view()),
    path("track-advertisement/", TrackAdvertisementApiView.as_view()),
    path("super-admin-advertisement-listing/", SuperAdminAdvertisementListingApiView.as_view()),
    path("super-admin-advertisement-detail/", SuperAdminAdvertisementDetailApiView.as_view()),
]
