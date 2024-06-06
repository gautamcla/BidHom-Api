# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.settings.views import *

urlpatterns = [
    path("get-state/", GetStateApiView.as_view()),
    path("get-country/", GetCountryApiView.as_view()),
    path("add-theme/", AddThemeApiView.as_view()),
    path("theme-status-change/", ThemeStatusChangeApiView.as_view()),
    path("admin-theme-listing/", AdminThemeListingApiView.as_view()),
    path("theme-listing/", ThemeListingApiView.as_view()),
    path("admin-user-theme-listing/", AdminUserThemeListingApiView.as_view()),
    path("admin-theme-detail/", AdminThemeDetailApiView.as_view()),
    path("add-subscription/", AddSubscriptionApiView.as_view()),
    path("admin-subscription-listing/", AdminSubscriptionListingApiView.as_view()),
    path("subscription-listing/", SubscriptionListingApiView.as_view()),
    path("admin-user-subscription-listing/", AdminUserSubscriptionListingApiView.as_view()),
    path("subscription-status-change/", SubscriptionStatusChangeApiView.as_view()),
    path("subscription-detail/", SubscriptionDetailApiView.as_view()),
    path("add-lookup-object/", AddLookupObjectApiView.as_view()),
    path("lookup-object-detail/", LookupObjectDetailApiView.as_view()),
    path("lookup-object-status-change/", LookupObjectStatusChangeApiView.as_view()),
    path("lookup-object-listing/", LookupObjectListingApiView.as_view()),
    path("add-lookup-status/", AddLookupStatusApiView.as_view()),
    path("lookup-status-change-status/", LookupStatusChangeStatusApiView.as_view()),
    path("admin-lookup-status-listing/", AdminLookupStatusListingApiView.as_view()),
    path("lookup-status-listing/", LookupStatusListingApiView.as_view()),
    path("lookup-status-detail/", LookupStatusDetailApiView.as_view()),
    path("add-lookup-object-status/", AddLookupObjectStatusApiView.as_view()),
    path("lookup-object-status-detail/", LookupObjectStatusDetailApiView.as_view()),
    path("lookup-object-change-status/", LookupObjectChangeStatusApiView.as_view()),
    path("lookup-object-status-listing/", LookupObjectStatusListingApiView.as_view()),
    path("add-plan-type/", AddPlanTypeApiView.as_view()),
    path("plan-type-detail/", PlanTypeDetailApiView.as_view()),
    path("plan-type-change-status/", PlanTypeChangeStatusApiView.as_view()),
    path("plan-type-listing/", PlanTypeListingApiView.as_view()),
    path("add-user-type/", AddUserTypeApiView.as_view()),
    path("user-type-detail/", UserTypeDetailApiView.as_view()),
    path("user-type-change-status/", UserTypeChangeStatusApiView.as_view()),
    path("user-type-listing/", UserTypeListingApiView.as_view()),
    path("add-property-type/", AddPropertyTypeApiView.as_view()),
    path("property-type-detail/", PropertyTypeDetailApiView.as_view()),
    path("property-type-change-status/", PropertyTypeChangeStatusApiView.as_view()),
    path("property-type-listing/", PropertyTypeListingApiView.as_view()),
    path("add-auction-type/", AddAuctionTypeApiView.as_view()),
    path("auction-type-detail/", AuctionTypeDetailApiView.as_view()),
    path("auction-type-change-status/", AuctionTypeChangeStatusApiView.as_view()),
    path("auction-type-listing/", AuctionTypeListingApiView.as_view()),
    path("subdomain-auction-type/", SubdomainAuctionTypeApiView.as_view()),
    path("add-documents-type/", AddDocumentsTypeApiView.as_view()),
    path("documents-type-detail/", DocumentsTypeDetailApiView.as_view()),
    path("documents-type-change-status/", DocumentsTypeChangeStatusApiView.as_view()),
    path("documents-type-listing/", DocumentsTypeListingApiView.as_view()),
    path("add-address-type/", AddAddressTypeApiView.as_view()),
    path("address-type-detail/", AddressTypeDetailApiView.as_view()),
    path("address-type-change-status/", AddressTypeChangeStatusApiView.as_view()),
    path("address-type-listing/", AddressTypeListingApiView.as_view()),
    path("add-upload-step/", AddUploadStepApiView.as_view()),
    path("upload-step-detail/", UploadStepDetailApiView.as_view()),
    path("upload-step-change-status/", UploadStepChangeStatusApiView.as_view()),
    path("upload-step-listing/", UploadStepListingApiView.as_view()),
    path("add-event/", AddEventApiView.as_view()),
    path("event-detail/", EventDetailApiView.as_view()),
    path("event-change-status/", EventChangeStatusApiView.as_view()),
    path("event-listing/", EventListingApiView.as_view()),
    path("add-site-setting/", AddSiteSettingApiView.as_view()),
    path("site-setting-detail/", SiteSettingDetailApiView.as_view()),
    path("site-setting-change-status/", SiteSettingChangeStatusApiView.as_view()),
    path("site-setting-listing/", SiteSettingListingApiView.as_view()),
    path("add-permission/", AddPermissionApiView.as_view()),
    path("permission-detail/", PermissionDetailApiView.as_view()),
    path("permission-change-status/", PermissionChangeStatusApiView.as_view()),
    path("permission-listing/", PermissionListingApiView.as_view()),
    path("agent-permission-listing/", AgentPermissionListingApiView.as_view()),
    path("add-property-features/", AddPropertyFeaturesApiView.as_view()),
    path("property-features-detail/", PropertyFeaturesDetailApiView.as_view()),
    path("property-features-change-status/", PropertyFeaturesChangeStatusApiView.as_view()),
    path("property-features-listing/", PropertyFeaturesListingApiView.as_view()),
    path("property-asset-listing/", PropertyAssetListingApiView.as_view()),
    path("timezone-listing/", TimezoneListingApiView.as_view()),
    path("admin-timezone-listing/", AdminTimezoneListingApiView.as_view()),
    path("admin-timezone-change-status/", AdminTimezoneChangeStatusApiView.as_view()),
    path("add-plan-pricing/", AddPlanPricingApiView.as_view()),
    path("admin-plan-pricing-listing/", AdminPlanPricingListingApiView.as_view()),
    path("plan-pricing-status-change/", PlanPricingStatusChangeApiView.as_view()),
    path("plan-pricing-detail/", PlanPricingDetailApiView.as_view()),
    path("subscription-list/", SubscriptionListApiView.as_view()),
    path("plan-type-list/", PlanTypeListApiView.as_view()),
    path("chat-count/", ChatCountApiView.as_view()),
    path("active-event-listing/", ActiveEventListingApiView.as_view()),
]
