# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.cms.views import *

urlpatterns = [
    path("add-cms/", AddCmsApiView.as_view()),
    path("cms-detail/", CmsDetailApiView.as_view()),
    path("cms-change-status/", CmsChangeStatusApiView.as_view()),
    path("admin-cms-listing/", AdminCmsListingApiView.as_view()),
    path("admin-article-listing/", AdminArticleListingApiView.as_view()),
    path("admin-add-article/", AdminAddArticleApiView.as_view()),
    path("admin-article-detail/", AdminArticleDetailApiView.as_view()),
    path("admin-article-change-status/", AdminArticleChangeStatusApiView.as_view()),
    path("get-page/", GetPageApiView.as_view()),
    path("get-auction-type/", GetAuctionTypeApiView.as_view()),
    path("about-detail/", AboutDetailApiView.as_view()),
    path("contact-detail/", ContactDetailApiView.as_view()),
    path("save-contact/", SaveContactApiView.as_view()),
    path("subdomain-contact-suggestion/", SubdomainContactSuggestionApiView.as_view()),
    path("video-tutorials/", VideoTutorialsApiView.as_view()),
    path("super-admin-video-tutorials-listing/", SuperAdminVideoTutorialsListingApiView.as_view()),
    path("super-admin-add-video-tutorials/", SuperAdminAddVideoTutorialsApiView.as_view()),
    path("super-admin-video-tutorials-detail/", SuperAdminVideoTutorialsDetailApiView.as_view()),
    path("subdomain-cms/", SubdomainCmsApiView.as_view()),
    path("subdomain-cms-update/", SubdomainCmsUpdateApiView.as_view()),
]
