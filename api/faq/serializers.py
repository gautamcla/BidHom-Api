# -*- coding: utf-8 -*-
"""Faq Serializer

"""
from rest_framework import serializers
from api.faq.models import *
from django.db.models import F


class FaqSerializer(serializers.ModelSerializer):
    """
    FaqSerializer
    """

    class Meta:
        model = Faq
        fields = "__all__"


class SubdomainFaqListingSerializer(serializers.ModelSerializer):
    """
    SubdomainFaqListingSerializer
    """
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")

    class Meta:
        model = Faq
        fields = ("id", "question", "answer", "status", "status_name", "added_on", "domain_name")


class SubdomainFaqDetailSerializer(serializers.ModelSerializer):
    """
    AdminFaqDetailSerializer
    """

    class Meta:
        model = Faq
        fields = "__all__"


class SuperAdminFaqListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminFaqListingSerializer
    """
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")

    class Meta:
        model = Faq
        fields = ("id", "question", "answer", "status", "status_name", "added_on", "domain_name")


class SuperAdminFaqDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminFaqDetailSerializer
    """

    class Meta:
        model = Faq
        fields = "__all__"


class FaqListingSerializer(serializers.ModelSerializer):
    """
    FaqListingSerializer
    """

    class Meta:
        model = Faq
        fields = ("id", "question", "answer")

