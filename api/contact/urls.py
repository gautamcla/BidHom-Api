# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.contact.views import *

urlpatterns = [
    path("super-admin-contact-listing/", SuperAdminContactListingView.as_view()),
    path("super-admin-contact-us-detail/", SuperAdminContactUsDetailApiView.as_view()),
    path("front-enquiry/", FrontEnquiryApiView.as_view()),
    path("chat-to-seller/", ChatToSellerApiView.as_view()),
    path("user-chat-master-listing/", UserChatMasterListingApiView.as_view()),
    path("user-chat-listing/", UserChatListingApiView.as_view()),
    path("user-send-chat/", UserSendChatApiView.as_view()),
    path("subdomain-chat-master-listing/", SubdomainChatMasterListingApiView.as_view()),
    path("broker-chat-master-listing/", BrokerChatMasterListingApiView.as_view()),
    path("subdomain-chat-listing/", SubdomainChatListingApiView.as_view()),
    path("subdomain-send-chat/", SubdomainSendChatApiView.as_view()),
    path("chat-to-agent/", ChatToAgentApiView.as_view()),
    path("mark-chat-read/", MarkChatReadApiView.as_view()),
    path("chat-to-buyer/", ChatToBuyerApiView.as_view()),
]
