# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.notifications.views import *

urlpatterns = [
    path("template-listing/", TemplateListingApiView.as_view()),
    path("add-template/", AddTemplateApiView.as_view()),
    path("template-detail/", TemplateDetailApiView.as_view()),
    path("template-change-status/", TemplateChangeStatusApiView.as_view()),
    path("subdomain-template-listing/", SubdomainTemplateListingApiView.as_view()),
    path("subdomain-add-template/", SubdomainAddTemplateApiView.as_view()),
    path("subdomain-template-detail/", SubdomainTemplateDetailApiView.as_view()),
    path("subdomain-template-suggestion/", SubdomainTemplateSuggestionApiView.as_view()),
    path("notification-detail/", NotificationDetailApiView.as_view()),
    path("notification-read/", NotificationReadApiView.as_view()),
    path("notification-count/", NotificationCountApiView.as_view()),
    path("notification-listing/", NotificationListingApiView.as_view()),
    path("template-list/", TemplateListApiView.as_view()),
    path("verify-email/", VerifyEmailApiView.as_view()),
]
