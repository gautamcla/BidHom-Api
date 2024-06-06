# -*- coding: utf-8 -*-
"""Users Serializer

"""
from rest_framework import serializers
# from api.users.models import *
from api.payments.models import *
from api.bid.models import *
from django.db.models import F
import requests
import urllib.parse
from django.conf import settings


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


class GetBusinessInfoSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = UserBusinessProfile
        fields = ("id", "first_name", "last_name", "company_name", "phone_no", "email", "address_first", "state",
                  "postal_code", "licence_no", "profile_image", "company_logo", "address", "mobile_no", "country")

    @staticmethod
    def get_profile_image(obj):
        try:
            profile_image = obj.user.profile_image
            upload = UserUploads.objects.get(id=int(profile_image))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_company_logo(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.company_logo))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            data = obj.user.profile_address_user.filter(user=obj.user_id, address_type=2, status=1)
            return AddressSerializer(data, many=True).data
        except Exception as exp:
            return []


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code")


class UserBusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBusinessProfile
        fields = '__all__'


class NetworkDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDomain
        fields = '__all__'


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'


class UserPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPayment
        fields = '__all__'


class PlanDashboardSerializer(serializers.ModelSerializer):
    """
    PlanDashboardSerializer
    """
    plan_name = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    plan_description = serializers.SerializerMethodField()
    upcoming_bill = serializers.SerializerMethodField()
    billing_history = serializers.SerializerMethodField()
    subscription_id = serializers.SerializerMethodField()
    theme_id = serializers.SerializerMethodField()
    theme_name = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ("id", "user_id", "plan_name", "cost", "plan_description", "upcoming_bill", "billing_history",
                  "subscription_id", "theme_id", "theme_name", "is_first_subscription")

    @staticmethod
    def get_plan_name(obj):
        try:
            return obj.opted_plan.subscription.plan_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_cost(obj):
        try:
            return int(obj.opted_plan.cost)
        except Exception as exp:
            return ""

    @staticmethod
    def get_plan_description(obj):
        try:
            return obj.opted_plan.subscription.plan_desc
        except Exception as exp:
            return ""

    @staticmethod
    def get_upcoming_bill(obj):
        try:
            data = {}
            if not obj.is_free:
                data['member_plan'] = obj.opted_plan.subscription.plan_name
                data['payment_date'] = obj.end_date
                data['amount'] = int(obj.opted_plan.cost)
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_billing_history(obj):
        try:
            data = {}
            # data = UserSubscription.objects.filter(user=obj.user_id, subscription_payment__id__gte=1).order_by("-id").values(member_plan=F("opted_plan__subscription__plan_name"), payment_date=F("subscription_payment__payment__added_on"), amount=F("subscription_payment__payment__payment_amount"), theme_name=F("theme__theme_name"))
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_subscription_id(obj):
        try:
            return obj.opted_plan.subscription.id
        except Exception as exp:
            return ""

    @staticmethod
    def get_theme_id(obj):
        try:
            data = UserTheme.objects.filter(domain=obj.user.site_id, status=1).last()
            return data.theme.id
        except Exception as exp:
            return ""

    @staticmethod
    def get_theme_name(obj):
        try:
            data = UserTheme.objects.filter(domain=obj.user.site_id, status=1).last()
            return data.theme.theme_name
        except Exception as exp:
            return ""


class PlanBillingHistorySerializer(serializers.ModelSerializer):
    """
    PlanBillingHistorySerializer
    """
    member_plan = serializers.CharField(source="opted_plan.subscription.plan_name", read_only=True, default="")
    payment_date = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    theme_name = serializers.DateTimeField(source="theme.theme_name", read_only=True, default="")

    class Meta:
        model = UserSubscription
        fields = ("id", "member_plan", "payment_date", "amount", "theme_name", "is_free")

    @staticmethod
    def get_payment_date(obj):
        try:
            return obj.subscription_payment.last().order.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_amount(obj):
        try:
            return obj.subscription_payment.last().order.amount
        except Exception as exp:
            return ""


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = '__all__'


class UserThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTheme
        fields = '__all__'


class SettingsDataSerializer(serializers.ModelSerializer):
    """
    SettingsDataSerializer
    """
    current_plan_id = serializers.SerializerMethodField()
    current_theme_id = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    is_agent = serializers.SerializerMethodField()
    is_broker = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("current_plan_id", "current_theme_id", "is_free", "is_agent", "is_broker", "permission")

    def get_current_plan_id(self, obj):
        try:
            site_id = self.context
            # data = UserSubscription.objects.filter(user__site=site_id, subscription_status=1, payment_status=1).first()
            data = UserSubscription.objects.filter(user__site=site_id, subscription_status=1, payment_status=1).last()
            # data = obj.user_subscription.filter(payment_status=1, subscription_status=1).first()
            return data.opted_plan.subscription_id
        except Exception as exp:
            return ""

    def get_current_theme_id(self, obj):
        try:
            site_id = self.context
            # data = UserTheme.objects.filter(domain=site_id, status=1).first()
            data = UserTheme.objects.filter(domain=site_id, status=1).last()
            return data.theme_id
        except Exception as exp:
            return ""

    def get_is_free(self, obj):
        try:
            site_id = self.context
            # data = obj.user_subscription.filter(payment_status=1, subscription_status=1).first()
            data = UserSubscription.objects.filter(domain=site_id, subscription_status=1, payment_status=1).last()
            return True if data.is_free == 1 else False
        except Exception as exp:
            return False

    def get_is_agent(self, obj):
        try:
            site_id = self.context
            data = obj.network_user.filter(domain=site_id, is_agent=1, status=1).first()
            return True if data is not None else False
        except Exception as exp:
            return False

    def get_is_broker(self, obj):
        try:
            site_id = self.context
            if obj.site_id == site_id:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_permission(self, obj):
        try:
            site_id = self.context
            # if obj.site_id is not None and obj.site_id == site_id:
            #     data = LookupPermission.objects.filter(permission_type__in=[2, 3]).values(permission_id=F("id"), permission_name=F("name"))
            # else:
            #     data = UserPermission.objects.filter(domain=site_id, user=obj.id, is_permission=1).values("permission_id", permission_name=F("permission__name"))
            data = UserPermission.objects.filter(domain=site_id, user=obj.id, is_permission=1).values("permission_id", permission_name=F("permission__name"))
            return data
        except Exception as exp:
            return {}


class AdminUserListingSerializer(serializers.ModelSerializer):
    """
    AdminUserListingSerializer
    """
    user_type = serializers.SerializerMethodField()
    status_id = serializers.CharField(source="status.id", read_only=True, default="")
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    network_domain = serializers.SerializerMethodField()
    domain_url = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    subscription_plan = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    user_network = serializers.SerializerMethodField()
    agent_network = serializers.SerializerMethodField()
    user_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "user_type", "email", "phone_no", "user_type", "status_id", "status_name", "added_on",
                  "network_domain", "domain_url", "first_name", "last_name", "licence_no", "subscription_plan", "theme",
                  "user_network", "agent_network", "activation_date", "email_verified_on", "user_subscription")

    @staticmethod
    def get_user_type(obj):
        try:
            return obj.user_type.user_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_network_domain(obj):
        try:
            return obj.site.domain_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_domain_url(obj):
        try:
            return obj.site.domain_url
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user_business_profile.first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_subscription_plan(obj):
        try:
            # return obj.user_subscription.filter(payment_status=1, subscription_status=1).first().opted_plan.subscription.plan_name
            return obj.user_subscription.filter(subscription_status=1).last().opted_plan.subscription.plan_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_theme(obj):
        try:
            return obj.site.user_theme_domain.filter(status=1).last().theme.theme_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_network(obj):
        try:
            data = []
            if obj.user_type_id == 1:
                return NetworkUser.objects.filter(user=obj.id).values('domain__domain_name', 'domain__domain_url')
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_agent_network(obj):
        try:
            data = []
            if obj.user_type_id == 2:
                return NetworkUser.objects.filter(user=obj.id, is_agent=1).values('domain__domain_name', 'domain__domain_url')
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_user_subscription(obj):
        try:
            if obj.stripe_customer_id is not None:
                return "Success"
            else:
                return "Pending"
            return data
        except Exception as exp:
            return "Pending"


class GetSiteDetailSerializer(serializers.ModelSerializer):
    """
    GetSiteDetailSerializer
    """
    site_id = serializers.CharField(source="id", read_only=True, default="")
    business_detail = serializers.SerializerMethodField()
    footer_images = serializers.SerializerMethodField()
    custom_site_settings = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    theme_folder = serializers.SerializerMethodField()
    plan_price_id = serializers.SerializerMethodField()
    previous_plan_price_id = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ("site_id", "domain_name", "domain_url", "business_detail", "footer_images", "custom_site_settings",
                  "theme", "theme_folder", "plan_price_id", "previous_plan_price_id", "email_verified")

    @staticmethod
    def get_business_detail(obj):
        try:
            return SiteBusinessDetailSerializer(obj.users_site_id.first().user_business_profile.first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_footer_images(obj):
        try:
            return obj.network_upload_domain.filter(upload_type=2, status=1).values(doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_custom_site_settings(obj):
        try:
            data_field = ["favicon", "website_title", "website_logo", "website_name"]
            data = obj.custom_site_settings.filter(is_active=1, settings_name__in=data_field)
            all_data = {}
            for i in data:
                if i.settings_name == "favicon":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name}
                    all_data[i.settings_name] = temp
                elif i.settings_name == "website_logo":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name}
                    all_data[i.settings_name] = temp
                else:
                    all_data[i.settings_name] = i.setting_value
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_theme(obj):
        try:
            return obj.user_theme_domain.filter(status=1).last().theme_id
        except Exception as exp:
            return 1

    @staticmethod
    def get_theme_folder(obj):
        try:
            return obj.user_theme_domain.filter(status=1).last().theme.theme_dir
        except Exception as exp:
            return "theme-1"

    @staticmethod
    def get_plan_price_id(obj):
        try:
            data = UserSubscription.objects.filter(domain=obj.id).last()
            return data.opted_plan_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_previous_plan_price_id(obj):
        try:
            data = UserSubscription.objects.filter(domain=obj.id).last()
            return data.previous_plan_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_email_verified(obj):
        try:
            data = Users.objects.filter(site_id=obj.id, status_id=1).first()
            return data.email_verified_on
        except Exception as exp:
            return ""


class SiteBusinessDetailSerializer(serializers.ModelSerializer):
    """
    SiteBusinessDetailSerializer
    """
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    address = serializers.SerializerMethodField()

    class Meta:
        model = UserBusinessProfile
        fields = ("id", "company_name", "email", "phone_no", "mobile_no", "address_first", "postal_code", "licence_no", "state",
                  "state_name", "address")

    @staticmethod
    def get_address(obj):
        try:
            data = obj.user.profile_address_user.filter(user=obj.user_id, address_type=2, status=1)
            return SiteAddressSerializer(data, many=True).data
        except Exception as exp:
            return []


class SiteAddressSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code")


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    AdminUserDetailSerializer
    """
    business_first_name = serializers.SerializerMethodField()
    business_last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    business_phone_no = serializers.SerializerMethodField()
    business_email = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    domain_name = serializers.SerializerMethodField()
    domain_url = serializers.SerializerMethodField()
    subscription_id = serializers.SerializerMethodField()
    theme_id = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    is_broker = serializers.SerializerMethodField()
    is_agent = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "site_id", "user_type", "email", "phone_no", "first_name", "last_name", "business_first_name",
                  "business_last_name", "company_name", "business_phone_no", "business_email", "licence_no",
                  "address_first", "state", "postal_code", "city", "domain_name", "domain_url", "subscription_id",
                  "theme_id", "profile_image", "company_logo", "address", "mobile_no", "is_broker", "is_agent")

    @staticmethod
    def get_business_first_name(obj):
        try:
            return obj.user_business_profile.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_business_last_name(obj):
        try:
            return obj.user_business_profile.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.user_business_profile.first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_business_phone_no(obj):
        try:
            return obj.user_business_profile.first().phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_business_email(obj):
        try:
            return obj.user_business_profile.first().email
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user_business_profile.first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.user_business_profile.first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.user_business_profile.first().state_id
        except Exception as exp:
            return 0

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.user_business_profile.first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_city(obj):
        try:
            return obj.user_business_profile.first().city
        except Exception as exp:
            return ""

    @staticmethod
    def get_domain_name(obj):
        try:
            return obj.site.domain_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_domain_url(obj):
        try:
            return obj.site.domain_url
        except Exception as exp:
            return ""

    @staticmethod
    def get_subscription_id(obj):
        try:
            return obj.user_subscription.filter(subscription_status=1).first().opted_plan.subscription_id
        except Exception as exp:
            return 0

    @staticmethod
    def get_theme_id(obj):
        try:
            return obj.site.user_theme_domain.filter(status=1).last().theme_id

        except Exception as exp:
            return 0

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_company_logo(obj):
        try:
            upload = obj.user_business_profile.first().company_logo
            data = UserUploads.objects.get(id=int(upload))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            address_type = obj.user_type_id
            return AdminUserAddressSerializer(obj.profile_address_user.filter(address_type=address_type, status=1), many=True).data
        except Exception as exp:
            return []

    @staticmethod
    def get_mobile_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().mobile_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_broker(obj):
        try:
            return True if obj.site_id is not None else False
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_agent(obj):
        try:
            data = obj.network_user.filter(is_agent=1).count()
            if obj.site_id is None and data > 0:
                return True
            else:
                return False
        except Exception as exp:
            return False


class AdminUserAddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code", "state_name")


class SubdomainAgentDetailSerializer(serializers.ModelSerializer):
    """
    SubdomainAgentDetailSerializer
    """
    first_name = serializers.CharField(default="")
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "company_name", "licence_no", "email", "phone_no", "mobile_no",
                  "address_first", "state", "postal_code", "status", "profile_image", "permission", "company_logo",
                  "address")

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_mobile_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().mobile_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().state_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.network_user.filter(is_agent=1).first().status_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    def get_permission(self, obj):
        try:
            user_data = {"site_id": self.context, "user_id": obj.id}
            data = LookupPermission.objects.filter(is_active=1, permission_type__in=[2, 3]).order_by("-id")
            return AgentPermissionSerializer(data, many=True, context=user_data).data
        except Exception as exp:
            return []

    @staticmethod
    def get_company_logo(obj):
        try:
            data = obj.user_business_profile.filter(status=1).first()
            upload = UserUploads.objects.get(id=int(data.company_logo))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return AgentDetailAddressSerializer(obj.profile_address_user.filter(address_type=2, status=1), many=True).data
        except Exception as exp:
            return []
        

class SubAdminDetailSerializer(serializers.ModelSerializer):
    """
    SubAdminDetailSerializer
    """
    first_name = serializers.CharField(default="")
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "company_name", "licence_no", "email", "phone_no", "mobile_no",
                  "address_first", "state", "postal_code", "status", "profile_image", "permission", "company_logo",
                  "address")

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_mobile_no(obj):
        try:
            return obj.mobile_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.profile_address_user.filter(status=1).first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.profile_address_user.filter(status=1).first().state_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.profile_address_user.filter(status=1).first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.status_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    def get_permission(self, obj):
        try:
            user_data = {"site_id": self.context, "user_id": obj.id}
            data = LookupPermission.objects.filter(is_active=1, permission_type__in=[2, 3]).order_by("-id")
            return AgentPermissionSerializer(data, many=True, context=user_data).data
        except Exception as exp:
            return []

    @staticmethod
    def get_company_logo(obj):
        try:
            return ""
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return AgentDetailAddressSerializer(obj.profile_address_user.filter(address_type=2, status=1), many=True).data
        except Exception as exp:
            return []        


class AgentDetailAddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code", "state_name")


class AgentPermissionSerializer(serializers.ModelSerializer):
    """
    AgentPermissionSerializer
    """
    is_permission = serializers.SerializerMethodField()

    class Meta:
        model = LookupPermission
        fields = ("id", "name", "is_permission")

    def get_is_permission(self, obj):
        try:
            data = obj.user_permission_permission.filter(domain=self.context['site_id'],
                                                         user=self.context['user_id']).first()
            return 0 if data is None else data.is_permission
        except Exception as exp:
            return 0


class MakeAgentDetailSerializer(serializers.ModelSerializer):
    """
    MakeAgentDetailSerializer
    """

    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "company_name", "licence_no", "email", "phone_no",
                  "mobile_no", "address_first", "state", "postal_code", "permission", "company_logo", "address")

    @staticmethod
    def get_first_name(obj):
        try:
            if obj.user_business_profile.filter(status=1).first() is not None and obj.user_business_profile.filter(status=1).first().first_name is not None:
                return obj.user_business_profile.filter(status=1).first().first_name
            else:
                return obj.first_name
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            if obj.user_business_profile.filter(status=1).first() is not None and obj.user_business_profile.filter(status=1).first().last_name is not None:
                return obj.user_business_profile.filter(status=1).first().last_name
            else:
                return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            if obj.user_business_profile.filter(status=1).first() is not None and obj.user_business_profile.filter(status=1).first().email is not None:
                return obj.user_business_profile.filter(status=1).first().email
            else:
                return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            if obj.user_business_profile.filter(status=1).first() is not None and obj.user_business_profile.filter(status=1).first().phone_no is not None:
                return obj.user_business_profile.filter(status=1).first().phone_no
            else:
                return obj.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_mobile_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().mobile_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().state_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    def get_permission(self, obj):
        try:
            user_data = {"site_id": self.context, "user_id": obj.id}
            data = LookupPermission.objects.filter(is_active=1, permission_type__in=[2, 3]).order_by("-id")
            return UserPermissionSerializer(data, many=True, context=user_data).data
        except Exception as exp:
            return []

    @staticmethod
    def get_company_logo(obj):
        try:
            data = obj.user_business_profile.filter(status=1).first()
            upload = UserUploads.objects.get(id=int(data.company_logo))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return MakeAgentAddressSerializer(obj.profile_address_user.filter(address_type=2, status=1), many=True).data
        except Exception as exp:
            return []


class MakeAgentAddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code", "state_name")


class UserPermissionSerializer(serializers.ModelSerializer):
    """
    UserPermissionSerializer
    """
    is_permission = serializers.SerializerMethodField()

    class Meta:
        model = LookupPermission
        fields = ("id", "name", "is_permission")

    def get_is_permission(self, obj):
        try:
            data = obj.user_permission_permission.filter(domain=self.context['site_id'], user=self.context['user_id']).first()
            return 0 if data is None else data.is_permission
        except Exception as exp:
            return 0


class SubdomainUserListingSerializer(serializers.ModelSerializer):
    """
    SubdomainUserListingSerializer
    """
    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    other_brokerage_name = serializers.SerializerMethodField()
    other_licence_number = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "email", "phone_no", "bids", "status", "status_name",
                  "added_on", "last_login", "described_by", "other_brokerage_name", "other_licence_number",
                  "user_details")

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.phone_no
        except Exception as exp:
            return ""

    def get_bids(self, obj):
        try:
            return Bid.objects.filter(domain=self.context, user=obj.id, bid_type__in=[2, 3]).count()
        except Exception as exp:
            return ""

    def get_other_brokerage_name(self, obj):
        try:
            return obj.network_user.filter(domain=self.context, status=1).first().brokerage_name
        except Exception as exp:
            return ""

    def get_other_licence_number(self, obj):
        try:
            return obj.network_user.filter(domain=self.context, status=1).first().licence_number
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_details(obj):
        try:
            profile_address = ProfileAddress.objects.filter(user=obj.id, address_type__in=[1]).first()
            user_detail = {}
            if profile_address is not None:
                user_detail['address_first'] = profile_address.address_first
                user_detail['address_second'] = profile_address.address_second
                user_detail['city'] = profile_address.city
                user_detail['state_name'] = profile_address.state.state_name
                user_detail['postal_code'] = profile_address.postal_code
            return user_detail
        except Exception as exp:
            return {}


class GetPersonalInfoSerializer(serializers.ModelSerializer):
    """
    GetPersonalInfoSerializer
    """
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "phone_no", "email", "profile_image")

    @staticmethod
    def get_profile_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.profile_image))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}


class SubdomainAgentListingSerializer(serializers.ModelSerializer):
    """
    SubdomainAgentListingSerializer
    """
    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    property_cnt = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    approval = serializers.CharField(default="Approved")
    is_upgrade = serializers.SerializerMethodField()
    user_status = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "company_name", "licence_no", "email", "phone_no",
                  "address_first", "state", "postal_code", "property_cnt", "added_on", "status", "approval", "last_login",
                  "is_upgrade", "user_status")

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.user_business_profile.filter(status=1).first().phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().state.iso_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_cnt(obj):
        try:
            return obj.property_listing_agent.exclude(status=5).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    def get_is_upgrade(self, obj):
        try:
            site_id = self.context
            return obj.network_user.filter(domain=site_id).first().is_upgrade
        except Exception as exp:
            return False

    def get_status(self, obj):
        try:
            site_id = self.context
            return obj.network_user.filter(domain=site_id).first().status.status_name
        except Exception as exp:
            return False
        

class SubAdminListingSerializer(serializers.ModelSerializer):
    """
    SubAdminListingSerializer
    """
    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    address_first = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    property_cnt = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    approval = serializers.CharField(default="Approved")
    is_upgrade = serializers.SerializerMethodField()
    user_status = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "company_name", "licence_no", "email", "phone_no",
                  "address_first", "state", "postal_code", "property_cnt", "added_on", "status", "approval", "last_login",
                  "is_upgrade", "user_status")

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address_first(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_state(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().state.iso_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_postal_code(obj):
        try:
            return obj.profile_address_user.filter(address_type=2, status=1).first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_cnt(obj):
        try:
            return obj.property_listing_agent.exclude(status=5).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    def get_is_upgrade(self, obj):
        try:
            return False
        except Exception as exp:
            return False

    def get_status(self, obj):
        try:
            site_id = self.context
            return obj.network_user.filter(domain=site_id).first().status.status_name
        except Exception as exp:
            return False   


class NetworkUserSerializer(serializers.ModelSerializer):
    """
    NetworkUserSerializer
    """

    class Meta:
        model = NetworkUser
        fields = "__all__"


class CustomSiteSettingsSerializer(serializers.ModelSerializer):
    """
    CustomSiteSettingsSerializer
    """

    class Meta:
        model = CustomSiteSettings
        fields = "__all__"


class SubdomainWebsiteDetailSerializer(serializers.ModelSerializer):
    """
    SubdomainWebsiteDetailSerializer
    """
    site_id = serializers.IntegerField(source="id", read_only=True, default="")
    # custom_site_settings = CustomSiteSettingsSerializer(many=True) # custom_site_settings is related key
    custom_site_settings = serializers.SerializerMethodField()
    banner_images = serializers.SerializerMethodField()
    footer_images = serializers.SerializerMethodField()
    auctions = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    social_account = serializers.SerializerMethodField()
    dashboard_numbers = serializers.SerializerMethodField()
    bot_setting = serializers.SerializerMethodField()
    mls_type = serializers.SerializerMethodField()
    mls_configuration = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ('site_id', "domain_type", "domain_name", "domain_url", "custom_site_settings", "banner_images",
                  "footer_images", "auctions", "expertise", "social_account", "dashboard_numbers", "bot_setting",
                  "mls_type", "mls_configuration")

    @staticmethod
    def get_custom_site_settings(obj):
        try:
            data = obj.custom_site_settings.filter(is_active=1)
            all_data = {}
            for i in data:
                if i.settings_name == "favicon":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name, "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                elif i.settings_name == "website_logo":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name, "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                else:
                    all_data[i.settings_name] = i.setting_value
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_banner_images(obj):
        try:
            return obj.network_upload_domain.filter(upload_type=1, status=1).values("id", "upload_type", "upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"), file_size=F("upload__file_size"), added_date=F("upload__added_on"))
        except Exception as exp:
            return []

    @staticmethod
    def get_footer_images(obj):
        try:
            return obj.network_upload_domain.filter(upload_type=2, status=1).values("id", "upload_type", "upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"), file_size=F("upload__file_size"), added_date=F("upload__added_on"))
        except Exception as exp:
            return []

    @staticmethod
    def get_auctions(obj):
        try:
            return obj.network_auction_domain.order_by("id").values("id", "auction_name", "upload_id", "status", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_expertise(obj):
        try:
            return obj.network_expertise_domain.order_by("id").values("id", "expertise_name", "upload_id", "status", "added_on", "expertise_icon_id", expertise_icon_name=F("expertise_icon__icon_name"), expertise_icon_type_id=F("expertise_icon__icon_type"), file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            print(exp)
            return []

    @staticmethod
    def get_social_account(obj):
        try:
            return obj.network_social_account_domain.filter(status=1).order_by("position").values("id", "account_type", "url", "status", "position")
        except Exception as exp:
            return []

    @staticmethod
    def get_dashboard_numbers(obj):
        try:
            return obj.dashboard_numbers_domain.order_by("id").values("id", "title", "value", "status")
        except Exception as exp:
            return []

    @staticmethod
    def get_bot_setting(obj):
        try:
            return obj.property_evaluator_setting_domain.filter(status=1).order_by("property_type").values("id", "property_type_id")
        except Exception as exp:
            return []

    @staticmethod
    def get_mls_type(obj):
        try:
            return MlsType.objects.filter(status=1).order_by("id").values("id", "name")
        except Exception as exp:
            return []

    @staticmethod
    def get_mls_configuration(obj):
        try:
            data = obj.network_mls_configuration.filter(status=1).first()
            all_data = {}
            if data is not None:
                all_data['id'] = data.id
                all_data['api_key'] = data.api_key
                all_data['domain_id'] = data.domain_id
                all_data['mls_type_id'] = data.mls_type_id
                all_data['originating_system'] = data.originating_system
            return all_data
        except Exception as exp:
            return {}


class NetworkArticlesSerializer(serializers.ModelSerializer):
    """
    NetworkArticlesSerializer
    """

    class Meta:
        model = NetworkArticles
        fields = "__all__"


class NetworkAuctionSerializer(serializers.ModelSerializer):
    """
    NetworkAuctionSerializer
    """

    class Meta:
        model = NetworkAuction
        fields = "__all__"


class NetworkExpertiseSerializer(serializers.ModelSerializer):
    """
    NetworkExpertiseSerializer
    """

    class Meta:
        model = NetworkExpertise
        fields = "__all__"


class NetworkSocialAccountSerializer(serializers.ModelSerializer):
    """
    NetworkSocialAccountSerializer
    """

    class Meta:
        model = NetworkSocialAccount
        fields = "__all__"


class DashboardNumbersSerializer(serializers.ModelSerializer):
    """
    DashboardNumbersSerializer
    """

    class Meta:
        model = DashboardNumbers
        fields = "__all__"


class AdminSubdomainListingSerializer(serializers.ModelSerializer):
    """
    AdminSubdomainListingSerializer
    """
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ('id', "domain_type", "domain_name", "domain_url", "is_active", "first_name", "last_name", "email",
                  "added_on", "owner_id")

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.users_site_id.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.users_site_id.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.users_site_id.first().email
        except Exception as exp:
            return ""

    @staticmethod
    def get_owner_id(obj):
        try:
            return obj.users_site_id.first().id
        except Exception as exp:
            return 0


class AdminSubdomainDetailSerializer(serializers.ModelSerializer):
    """
    AdminSubdomainDetailSerializer
    """
    site_id = serializers.IntegerField(source="id", read_only=True, default="")
    # custom_site_settings = CustomSiteSettingsSerializer(many=True) # custom_site_settings is related key
    custom_site_settings = serializers.SerializerMethodField()
    banner_images = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    footer_images = serializers.SerializerMethodField()
    # about_images = serializers.SerializerMethodField()
    auctions = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    social_account = serializers.SerializerMethodField()
    dashboard_numbers = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ('site_id', "domain_type", "domain_name", "domain_url", "custom_site_settings", "banner_images",
                  "articles", "footer_images", "auctions", "expertise", "social_account", "dashboard_numbers")

    @staticmethod
    def get_custom_site_settings(obj):
        try:
            data = obj.custom_site_settings.filter(is_active=1)
            all_data = {}
            for i in data:
                if i.settings_name == "favicon":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name, "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                elif i.settings_name == "website_logo":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name, "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                else:
                    all_data[i.settings_name] = i.setting_value
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_banner_images(obj):
        try:
            return obj.network_upload_domain.filter(upload_type=1, status=1).values("id", "upload_type", "upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"), file_size=F("upload__file_size"), added_date=F("upload__added_on"))
        except Exception as exp:
            return []

    @staticmethod
    def get_articles(obj):
        try:
            return obj.network_articles_domain.filter(status=1).values("id", "title", "description", "author_name", "author_image_id", article_image_id=F("upload"), image=F("upload__doc_file_name"), author_image_name=F("author_image__doc_file_name"), article_image_name=F("upload__doc_file_name"), author_image_bucket_name=F("author_image__bucket_name"), article_image_name_bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_footer_images(obj):
        try:
            return obj.network_upload_domain.filter(upload_type=2, status=1).values("id", "upload_type", "upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"), file_size=F("upload__file_size"), added_date=F("upload__added_on"))
        except Exception as exp:
            return []

    @staticmethod
    def get_auctions(obj):
        try:
            return obj.network_auction_domain.order_by("id").values("id", "auction_name", "upload_id", "status", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_expertise(obj):
        try:
            return obj.network_expertise_domain.order_by("id").values("id", "expertise_name", "upload_id", "status", "added_on", "expertise_icon_id", expertise_icon_name=F("expertise_icon__icon_name"), expertise_icon_type_id=F("expertise_icon__icon_type"), file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_social_account(obj):
        try:
            return obj.network_social_account_domain.filter(status=1).order_by("position").values("id", "account_type", "url", "status", "position")
        except Exception as exp:
            return []

    @staticmethod
    def get_dashboard_numbers(obj):
        try:
            return obj.dashboard_numbers_domain.order_by("id").values("id", "title", "value", "status")
        except Exception as exp:
            return []

    # @staticmethod
    # def get_about_images(obj):
    #     try:
    #         return obj.network_upload_domain.filter(upload_type=3, status=1).values("id", "upload_type", "upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"), file_size=F("upload__file_size"), added_date=F("upload__added_on"))
    #     except Exception as exp:
    #         return []


class UserUploadsSerializer(serializers.ModelSerializer):
    """
    UserUploadsSerializer
    """

    class Meta:
        model = UserUploads
        fields = "__all__"


class NetworkUploadSerializer(serializers.ModelSerializer):
    """
    NetworkUploadSerializer
    """

    class Meta:
        model = NetworkUpload
        fields = "__all__"


class ArticleListingSerializer(serializers.ModelSerializer):
    """
    ArticleListingSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    category_name = serializers.CharField(source="asset.name", read_only=True, default="")

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status", "added_on",
                  "publish_date", "category_name")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_article_image(obj):
        try:
            data = {}
            data['image_name'] = obj.upload.doc_file_name
            data['bucket_name'] = obj.upload.bucket_name
            return data
        except Exception as exp:
            return {}


class SubdomainUserDetailSerializer(serializers.ModelSerializer):
    """
    SubdomainUserDetailSerializer
    """

    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "email", "phone_no")

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.phone_no
        except Exception as exp:
            return ""


class AddArticleSerializer(serializers.ModelSerializer):
    """
    AddArticleSerializer
    """

    class Meta:
        model = NetworkArticles
        fields = "__all__"


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    ArticleDetailSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status",
                  "publish_date", "asset")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            data['upload_id'] = obj.author_image_id
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_article_image(obj):
        try:
            data = {}
            data['image_name'] = obj.upload.doc_file_name
            data['bucket_name'] = obj.upload.bucket_name
            data['upload_id'] = obj.upload_id
            return data
        except Exception as exp:
            return {}


class ContactUsListingSerializer(serializers.ModelSerializer):
    """
    ContactUsListingSerializer
    """

    class Meta:
        model = ContactUs
        fields = ("id", "first_name", "last_name", "email", "phone_no", "user_type", "message", "added_on")


class AdminArticleListingSerializer(serializers.ModelSerializer):
    """
    AdminArticleListingSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    category_name = serializers.CharField(source="asset.name", read_only=True, default="")
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status", "added_on",
                  "publish_date", "category_name", "domain_name", "asset")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_article_image(obj):
        try:
            data = {}
            data['image_name'] = obj.upload.doc_file_name
            data['bucket_name'] = obj.upload.bucket_name
            return data
        except Exception as exp:
            return {}


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    UserProfileDetailSerializer
    """

    profile_image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    brokerage_name = serializers.SerializerMethodField()
    licence_number = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "profile_image", "first_name", "last_name", "email", "phone_no", "address", "described_by",
                  "brokerage_name", "licence_number")

    @staticmethod
    def get_profile_image(obj):
        try:
            data = UserUploads.objects.get(id=int(obj.profile_image))
            all_data = {"upload_id": data.id, "doc_file_name": data.doc_file_name, "bucket_name": data.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_address(obj):
        try:
            data = {}
            address = obj.profile_address_user.filter(address_type=1, status=1).first()
            if address is not None:
                data['address_first'] = address.address_first
                data['state'] = address.state_id
                data['postal_code'] = address.postal_code
                data['city'] = address.city
                data['country'] = address.country_id
            return data
        except Exception as exp:
            return {}

    def get_brokerage_name(self, obj):
        try:
            return obj.network_user.filter(domain=self.context).first().brokerage_name
        except Exception as exp:
            return ""

    def get_licence_number(self, obj):
        try:
            return obj.network_user.filter(domain=self.context).first().licence_number
        except Exception as exp:
            return ""


class AgentListSerializer(serializers.ModelSerializer):
    """
    AgentListSerializer
    """
    image = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    licence_no = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    mobile_no = serializers.SerializerMethodField()
    property_count = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = NetworkUser
        fields = ('user_id', "image", "first_name", "last_name", "company_name", "email", "licence_no", "phone_no",
                  "property_count", "mobile_no", "address")

    @staticmethod
    def get_image(obj):
        try:
            profile_image = obj.user.profile_image
            upload = UserUploads.objects.get(id=int(profile_image))
            data = {
                "upload_id": upload.id,
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_first_name(obj):
        try:
            return obj.user.user_business_profile.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            return obj.user.user_business_profile.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.user.user_business_profile.first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.user.user_business_profile.first().email
        except Exception as exp:
            return ""

    @staticmethod
    def get_licence_no(obj):
        try:
            return obj.user.user_business_profile.first().licence_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.user.user_business_profile.first().phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_mobile_no(obj):
        try:
            return obj.user.user_business_profile.first().mobile_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_count(obj):
        try:
            return obj.user.property_listing_agent.filter(status=1, domain=obj.domain_id).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_address(obj):
        try:
            data = obj.user.profile_address_user.filter(user=obj.user_id, address_type=2, status=1)
            return AgentAddressSerializer(data, many=True).data
        except Exception as exp:
            return []


class AgentAddressSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code")


class ProfileAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAddress
        fields = '__all__'


class SubdomainUserRegistrationSerializer(serializers.ModelSerializer):
    """
    SubdomainUserRegistrationSerializer
    """
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    is_reviewed_name = serializers.SerializerMethodField()
    is_approved_name = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    bid_limit = serializers.SerializerMethodField()
    sale_type = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    stage = serializers.CharField(source="property.status.status_name", read_only=True, default="")
    current_bid = serializers.SerializerMethodField()
    auction_start = serializers.SerializerMethodField()
    auction_end = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "property_address_one", "property_city", "property_state", "property_postal_code",
                  "is_reviewed_name", "is_approved_name", "is_reviewed", "is_approved", "bid_count", "bid_limit",
                  "sale_type", "stage", "current_bid", "auction_start", "auction_end", "property_image", "property_id")

    @staticmethod
    def get_is_reviewed_name(obj):
        try:
            if obj.is_reviewed == 1:
                return "Reviewed"
            else:
                return "Not Reviewed"
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_approved_name(obj):
        try:
            approval = {1: "Pending", 2: "Not Reviewed", 3: "Declined", 4: "Not Interested"}
            if obj.is_approved == 2 and obj.is_reviewed:
                return "Approved"
            else:
                return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""
        # try:
        #     approval_list = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
        #     return approval_list[obj.is_approved]
        # except Exception as exp:
        #     return ""

    @staticmethod
    def get_bid_count(obj):
        try:
            return obj.property.bid_property.filter(user=obj.user_id, is_canceled=0, bid_type__in=[2, 3]).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_limit(obj):
        try:
            return obj.bid_limit_registration.filter(status=1).last().approval_limit
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_bid(obj):
        try:
            return Bid.objects.filter(property=obj.property_id, is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_start(obj):
        try:
            return obj.property.property_auction.last().start_date

        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_end(obj):
        try:
            return obj.property.property_auction.last().end_date

        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class PlanBillingDetailSerializer(serializers.ModelSerializer):
    """
    PlanBillingDetailSerializer
    """
    member_plan = serializers.CharField(source="opted_plan.subscription.plan_name", read_only=True, default="")
    payment_date = serializers.SerializerMethodField()
    theme_name = serializers.DateTimeField(source="theme.theme_name", read_only=True, default="")
    user_detail = serializers.SerializerMethodField()
    payment_detail = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = ("id", "member_plan", "payment_date", "theme_name", "user_detail", "payment_detail", "invoice",
                  "customer")

    @staticmethod
    def get_payment_date(obj):
        try:
            return obj.subscription_payment.last().order.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_amount(obj):
        try:
            return obj.subscription_payment.last().order.amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_detail(obj):
        try:
            data = {}
            data['first_name'] = obj.user.first_name if obj.user is not None else ""
            data['last_name'] = obj.user.last_name if obj.user is not None else ""
            data['email'] = obj.user.email if obj.user is not None else ""
            data['phone_no'] = obj.user.phone_no if obj.user is not None else ""
            address = obj.user.profile_address_user.filter(address_type=1).first()
            data['address_first'] = address.address_first if address is not None else ""
            data['city'] = address.city if address is not None else ""
            data['state'] = address.state.state_name if address is not None else ""
            # data['phone_no'] = address.phone_no if address is not None else ""
            data['postal_code'] = address.postal_code if address is not None else ""
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_payment_detail(obj):
        try:
            data = {}
            payment = obj.subscription_payment.last()
            data['amount'] = payment.order.amount if payment is not None else ""
            data['payment_terms'] = "Credit Card"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_invoice(obj):
        try:
            return "INV000"+str(obj.id)
        except Exception as exp:
            return ""

    @staticmethod
    def get_customer(obj):
        try:
            return "CUST000" + str(obj.user_id)
        except Exception as exp:
            return ""


class AddTestimonialSerializer(serializers.ModelSerializer):
    """
    AddTestimonialSerializer
    """

    class Meta:
        model = NetworkTestimonials
        fields = "__all__"


class TestimonialsListingSerializer(serializers.ModelSerializer):
    """
    TestimonialsListingSerializer
    """
    author_image = serializers.SerializerMethodField()
    status = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = NetworkTestimonials
        fields = ("id", "title", "description", "author_name", "author_image", "status", "added_on", "type")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            return data
        except Exception as exp:
            return {}


class TestimonialDetailSerializer(serializers.ModelSerializer):
    """
    TestimonialDetailSerializer
    """
    author_image = serializers.SerializerMethodField()

    class Meta:
        model = NetworkTestimonials
        fields = ("id", "title", "description", "author_name", "author_image", "status", "type")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            data['upload_id'] = obj.author_image_id
            return data
        except Exception as exp:
            return {}


class FrontTestimonialSerializer(serializers.ModelSerializer):
    """
    FrontTestimonialSerializer
    """
    author_image = serializers.SerializerMethodField()

    class Meta:
        model = NetworkTestimonials
        fields = ("id", "title", "description", "author_name", "author_image", "status", "type")

    @staticmethod
    def get_author_image(obj):
        try:
            data = {}
            data['image_name'] = obj.author_image.doc_file_name
            data['bucket_name'] = obj.author_image.bucket_name
            data['upload_id'] = obj.author_image_id
            return data
        except Exception as exp:
            return {}


class UpdateDashboardMapSerializer(serializers.ModelSerializer):
    """
    UpdateDashboardMapSerializer
    """
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "state_name", "name", "location")

    @staticmethod
    def get_name(obj):
        try:
            name = obj.address_one
            name += ", " + obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_location(obj):
        try:
            name = obj.address_one
            name += ", " + obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            api_key = settings.GOOGLE_API_KEY
            api_response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(name, api_key))
            api_response_dict = api_response.json()
            data = {"lat": api_response_dict['results'][0]['geometry']['location']['lat'], "lon": api_response_dict['results'][0]['geometry']['location']['lng']}
            return data
        except Exception as exp:
            return ""


class AddDummyPropertySerializer(serializers.ModelSerializer):
    """
    AddDummyPropertySerializer
    """

    class Meta:
        model = PropertyListing
        fields = "__all__"


class AddDummyAuctionSerializer(serializers.ModelSerializer):
    """
    AddDummyAuctionSerializer
    """

    class Meta:
        model = PropertyAuction
        fields = "__all__"


class AddPropertyUploadsSerializer(serializers.ModelSerializer):
    """
    AddPropertyUploadsSerializer
    """

    class Meta:
        model = PropertyUploads
        fields = "__all__"


class GetDomainUserDetailSerializer(serializers.ModelSerializer):
    """
    GetDomainUserDetailSerializer
    """

    class Meta:
        model = Users
        fields = ("id", "site", "stripe_customer_id", "stripe_subscription_id")


class NetworkPaymentCredentialSerializer(serializers.ModelSerializer):
    """
    NetworkPaymentCredentialSerializer
    """

    class Meta:
        model = NetworkPaymentCredential
        fields = "__all__"        

