# -*- coding: utf-8 -*-
"""Payments Serializer

"""
from rest_framework import serializers
from api.payments.models import *
from django.db.models import F
from api.property.models import *


class PaymentSubscriptionDetailSerializer(serializers.ModelSerializer):
    """
    PaymentSubscriptionDetailSerializer
    """
    subscription_name = serializers.CharField(source="subscription.plan_name", default="", read_only=True)

    class Meta:
        model = PlanPricing
        fields = ('id', 'subscription_id', 'cost', 'subscription_name')


class CreatePaymentDataSerializer(serializers.ModelSerializer):
    """
    CreatePaymentDataSerializer
    """
    cost = serializers.CharField(source="plan_price.cost", default="", read_only=True)
    stripe_button_id = serializers.CharField(source="plan_price.stripe_button_id", default="", read_only=True)
    theme_name = serializers.CharField(source="theme.theme_name", default="", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan_name", default="", read_only=True)
    stripe_active_button_id = serializers.CharField(source="plan_price.stripe_active_button_id", default="", read_only=True)

    class Meta:
        model = PaymentDetail
        fields = ('id', 'domain_id', 'user_id', 'subscription_id', 'plan_price_id', 'theme_id', 'cost',
                  'stripe_button_id', 'theme_name', 'plan_name', 'stripe_active_button_id')


class OrderSuccessSerializer(serializers.ModelSerializer):
    """
    OrderSuccessSerializer
    """
    user_id = serializers.CharField(source="order.user_id", default="", read_only=True)
    domain_id = serializers.CharField(source="order.domain_id", default="", read_only=True)

    class Meta:
        model = OrderDetail
        fields = ("id", "subscription_id", "plan_price_id", "theme_id", "order_id", "user_id", "domain_id")


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = '__all__'


class UserThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTheme
        fields = '__all__'


class SuccessPaymentDetailSerializer(serializers.ModelSerializer):
    """
    SuccessPaymentDetailSerializer
    """
    order_id = serializers.SerializerMethodField()
    transaction_id = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPayment
        fields = ("id", "order_id", "transaction_id", "cost")

    @staticmethod
    def get_order_id(obj):
        try:
            return "000" + str(obj.subscription_id) if obj.subscription_id is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_transaction_id(obj):
        try:
            return "IC-" + str(obj.order_id) if obj.order_id is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_cost(obj):
        try:
            return obj.order.amount
        except Exception as exp:
            return ""


class AdminTransactionListingSerializer(serializers.ModelSerializer):
    """
    AdminTransactionListingSerializer
    """
    domain_name = serializers.CharField(source="domain.domain_name", default="", read_only=True)
    payment_type = serializers.CharField(source="payment_type.type_name", default="", read_only=True)
    card_number = serializers.SerializerMethodField()
    subscription_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "domain_name", "payment_type", "card_number", "card_network", "amount", "subscription_name",
                  "added_on")

    @staticmethod
    def get_card_number(obj):
        try:
            return 12 * "*" + str(obj.card_last_four)
        except Exception as exp:
            return ""

    @staticmethod
    def get_subscription_name(obj):
        try:
            return obj.order_detail.last().subscription.plan_name
        except Exception as exp:
            return ""


class CheckPaymentSerializer(serializers.ModelSerializer):
    """
    CheckPaymentSerializer
    """
    cost = serializers.CharField(source="plan_price.cost", default="", read_only=True)
    stripe_button_id = serializers.CharField(source="plan_price.stripe_button_id", default="", read_only=True)
    theme_name = serializers.CharField(source="theme.theme_name", default="", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan_name", default="", read_only=True)

    class Meta:
        model = PaymentDetail
        fields = ('id', 'domain_id', 'user_id', 'subscription_id', 'plan_price_id', 'theme_id', 'cost',
                  'stripe_button_id', 'theme_name', 'plan_name')


class StripePaymentDetailSerializer(serializers.ModelSerializer):
    """
    StripePaymentDetailSerializer
    """

    class Meta:
        model = PlanPricing
        fields = ('id', 'cost', 'stripe_price_id', 'stripe_button_id', 'stripe_payment_link', 'stripe_active_price_id',
                  'stripe_active_button_id', 'stripe_active_payment_link')
        

class PaymentListingDepositDetailSerializer(serializers.ModelSerializer):
    """
    PaymentListingDepositDetailSerializer
    """
    is_deposit_required = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ('id', 'is_deposit_required', 'deposit_amount')

    @staticmethod
    def get_is_deposit_required(obj):
        try:
            users = Users.objects.filter(site=obj.domain_id, status=1).last()
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0,
                                                   status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0,
                                                       is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                           is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                       is_agent=0, status=1, is_deposit_required=1).last()

            if data is not None:
                return data.is_deposit_required
            else:
                return 0
        except Exception as exp:
            return 0

    @staticmethod
    def get_deposit_amount(obj):
        try:
            users = Users.objects.filter(site=obj.domain_id, status=1).last()
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0,
                                                   status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0,
                                                       is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                           is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                       is_agent=0, status=1, is_deposit_required=1).last()

            if data is not None and data.is_deposit_required:
                return int(data.deposit_amount)
            else:
                return ""
        except Exception as exp:
            return ""     

