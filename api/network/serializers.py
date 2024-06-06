# -*- coding: utf-8 -*-
"""Network Serializer

"""
from rest_framework import serializers
from api.payments.models import *
from django.db.models import F


class AdminActiveDomainSerializer(serializers.ModelSerializer):
    """
    AdminActiveDomainSerializer
    """

    class Meta:
        model = NetworkDomain
        fields = ("id", "domain_name")


class AdminActiveNetworkAgentSerializer(serializers.ModelSerializer):
    """
    AdminActiveNetworkAgentSerializer
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "name")

    @staticmethod
    def get_name(obj):
        try:
            return obj.user_business_profile.first().first_name + " " + obj.user_business_profile.first().last_name + "(" + obj.user_business_profile.first().email + ")"
        except Exception as exp:
            return ""

