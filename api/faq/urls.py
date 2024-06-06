# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.faq.views import *

urlpatterns = [
    path("super-admin-add-faq/", SuperAdminAddFaqView.as_view()),
    path("super-admin-faq-detail/", SuperAdminFaqDetailApiView.as_view()),
    path("super-admin-faq-listing/", SuperAdminFaqListingApiView.as_view()),
    path("subdomain-add-faq/", SubdomainAddFaqView.as_view()),
    path("subdomain-faq-detail/", SubdomainFaqDetailApiView.as_view()),
    path("subdomain-faq-listing/", SubdomainFaqListingApiView.as_view()),
    path("faq-listing/", FaqListingApiView.as_view()),
]
