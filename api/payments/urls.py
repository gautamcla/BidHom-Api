# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.payments.views import *

urlpatterns = [
    path("payment-subscription-detail/", PaymentSubscriptionDetailApiView.as_view()),
    path("create-order/", CreateOrderApiView.as_view()),
    path("create-payment-detail/", CreatePaymentDetailApiView.as_view()),
    path("create-payment-data/", CreatePaymentDataApiView.as_view()),
    path("order-success/", OrderSuccessApiView.as_view()),
    path("after-payment-change-plan/", AfterPaymentChangePlanApiView.as_view()),
    path("success-payment-detail/", SuccessPaymentDetailApiView.as_view()),
    path("change-plan-subscription/", ChangePlanSubscriptionApiView.as_view()),
    path("admin-transaction-listing/", AdminTransactionListingApiView.as_view()),
    path("check-payment/", CheckPaymentApiView.as_view()),
    path("plan-upgrade-after-payment/", PlanUpgradeAfterPaymentApiView.as_view()),
    path("check-payment-success/", CheckPaymentSuccessApiView.as_view()),
    path("check-global-payment/", CheckGlobalPaymentApiView.as_view()),
    path("stripe-payment-detail/", StripePaymentDetailApiView.as_view()),
    path("check-payment-subscription/", CheckPaymentSubscriptionApiView.as_view()),
    path("payment-listing-deposit-detail/", PaymentListingDepositDetailApiView.as_view()),
]
