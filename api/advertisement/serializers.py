# -*- coding: utf-8 -*-
"""Advertisement Serializer

"""
from rest_framework import serializers
from api.advertisement.models import *
from django.db.models import F


class AdvertisementSerializer(serializers.ModelSerializer):
    """
    AdvertisementSerializer
    """

    class Meta:
        model = Advertisement
        fields = "__all__"


class TrackAdvertisementSerializer(serializers.ModelSerializer):
    """
    TrackAdvertisementSerializer
    """

    class Meta:
        model = TrackAdvertisement
        fields = "__all__"


class SuperAdminAdvertisementListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminAdvertisementListingSerializer
    """
    domain = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    total_add_view = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = ("id", "domain", "company_name", "url", "added_on", "status", "total_add_view")

    @staticmethod
    def get_total_add_view(obj):
        try:
            return obj.track_advertisement.count()
        except Exception as exp:
            return ""


class SuperAdminAdvertisementDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminAdvertisementDetailSerializer
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = ("id", "domain", "company_name", "url", "image", "added_by", "updated_by", "status")

    @staticmethod
    def get_image(obj):
        try:
            data = {
                "id": obj.image.id,
                "doc_file_name": obj.image.doc_file_name,
                "bucket_name": obj.image.bucket_name
            }
            return data
        except Exception as exp:
            return {}



