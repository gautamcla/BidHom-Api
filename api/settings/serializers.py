# -*- coding: utf-8 -*-
"""Settings Serializer

"""
from rest_framework import serializers
from api.settings.models import *
from api.users.models import *


class SubscriptionPlanListingSerializer(serializers.ModelSerializer):
    """
    SubscriptionPlanListingSerializer
    """
    cost = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'plan_name', 'plan_desc', 'is_active', 'cost')

    @staticmethod
    def get_cost(obj):
        try:
            return obj.plan_pricing_subscription.first().cost
        except Exception as exp:
            return ""


class SubscriptionListingSerializer(serializers.ModelSerializer):
    """
    SubscriptionListingSerializer
    """
    cost = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    is_current_plan = serializers.SerializerMethodField()
    plan_price_id = serializers.SerializerMethodField()
    stripe_button_id = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'plan_name', 'plan_desc', 'is_active', 'cost', 'benefits', 'is_current_plan', 'is_free',
                  'plan_price_id', 'stripe_button_id')

    @staticmethod
    def get_cost(obj):
        try:
            return int(obj.plan_pricing_subscription.first().cost)
        except Exception as exp:
            return ""

    @staticmethod
    def get_benefits(obj):
        try:
            return obj.plan_pricing_subscription.plan_type.plan_benefits_plan.first().benefits
        except Exception as exp:
            return ""

    def get_is_current_plan(self, obj):
        try:
            user_id = self.context
            subscription_id = obj.plan_pricing_subscription.first().id
            user_subscription = UserSubscription.objects.filter(user=user_id, subscription_status=1).last()
            if subscription_id == user_subscription.opted_plan_id:
                return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_plan_price_id(obj):
        try:
            return obj.plan_pricing_subscription.filter(is_active=1).last().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_stripe_button_id(obj):
        try:
            return obj.plan_pricing_subscription.first().stripe_button_id
        except Exception as exp:
            return ""


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """
    SubscriptionDetailSerializer
    """
    cost = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'plan_name', 'plan_desc', 'is_active', 'cost')

    @staticmethod
    def get_cost(obj):
        try:
            return obj.plan_pricing_subscription.first().cost
        except Exception as exp:
            return ""


class ThemesAvailableSerializer(serializers.ModelSerializer):
    """
    ThemesAvailableSerializer
    """
    class Meta:
        model = ThemesAvailable
        fields = "__all__"


class AdminThemeDetailSerializer(serializers.ModelSerializer):
    """
    AdminThemeDetailSerializer
    """
    class Meta:
        model = ThemesAvailable
        fields = "__all__"


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    SubscriptionPlanSerializer
    """
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class PlanPricingSerializer(serializers.ModelSerializer):
    """
    PlanBenefitsSerializer
    """
    class Meta:
        model = PlanPricing
        fields = "__all__"


class LookupStatusSerializer(serializers.ModelSerializer):
    """
    LookupStatusSerializer
    """

    class Meta:
        model = LookupStatus
        fields = "__all__"


class LookupStatusDetailSerializer(serializers.ModelSerializer):
    """
    LookupStatusDetailSerializer
    """

    class Meta:
        model = LookupStatus
        fields = ('id', "status_name", "is_active")


class LookupStatusDetailLookupObjectStatusSerializer(serializers.ModelSerializer):
    """
    LookupStatusDetailLookupObjectStatusSerializer
    """
    id = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = LookupObjectStatus
        fields = ("id", "object_name", "is_active")

    @staticmethod
    def get_id(obj):
        try:
            return obj.object.id
        except Exception as exp:
            return ""

    @staticmethod
    def get_object_name(obj):
        try:
            return obj.object.object_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_active(obj):
        try:
            return obj.object.is_active
        except Exception as exp:
            return ""


class AdminTimezoneListingSerializer(serializers.ModelSerializer):
    """
    AdminTimezoneListingSerializer
    """

    class Meta:
        model = LookupTimezone
        fields = "__all__"


class LookupObjectStatusListingSerializer(serializers.ModelSerializer):
    """
    LookupObjectStatusListingSerializer
    """
    status_name = serializers.SerializerMethodField()
    status_object = serializers.SerializerMethodField()
    lookup_status_id = serializers.IntegerField(source="status_id", read_only=True, default="")
    lookup_object_id = serializers.IntegerField(source="object_id", read_only=True, default="")

    class Meta:
        model = LookupObjectStatus
        fields = ("id", "status_name", "status_object", "is_active", "lookup_status_id", "lookup_object_id")

    @staticmethod
    def get_status_name(obj):
        try:
            return obj.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_status_object(obj):
        try:
            return obj.object.object_name
        except Exception as exp:
            return ""


class AdminPlanPricingListingSerializer(serializers.ModelSerializer):
    """
    AdminPlanPricingListingSerializer
    """
    name = serializers.CharField(source="subscription.plan_name", read_only=True, default="")
    plan_type = serializers.CharField(source="plan_type.type_name", read_only=True, default="")

    class Meta:
        model = PlanPricing
        fields = ("id", "cost", "subscription", "plan_type", "cost", "is_active", "name", "plan_type", "plan_type_id")


class PlanPricingDetailSerializer(serializers.ModelSerializer):
    """
    PlanPricingDetailSerializer
    """

    class Meta:
        model = PlanPricing
        fields = ("id", "cost", "subscription", "plan_type", "cost", "is_active")