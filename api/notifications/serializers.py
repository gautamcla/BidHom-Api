# -*- coding: utf-8 -*-
"""Notification Serializer

"""
from rest_framework import serializers
from api.notifications.models import *
from django.db.models import F


class TemplateListingSerializer(serializers.ModelSerializer):
    """
    TemplateListingSerializer
    """
    event_name = serializers.CharField(source="event.event_name", read_only=True, default="")
    event_slug = serializers.CharField(source="event.slug", read_only=True, default="")
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    domain = serializers.CharField(source="site.domain_name", read_only=True, default="")

    class Meta:
        model = NotificationTemplate
        fields = ("id", "status_name", "domain", "event_name", "event_slug", "status", "email_subject", "added_on")


class AddTemplateSerializer(serializers.ModelSerializer):
    """
    AddTemplateSerializer
    """

    class Meta:
        model = NotificationTemplate
        fields = "__all__"


class TemplateDetailSerializer(serializers.ModelSerializer):
    """
    TemplateDetailSerializer
    """

    class Meta:
        model = NotificationTemplate
        fields = ("id", "site_id", "event_id", "email_subject", "email_content", "notification_text",
                  "push_notification_text", "status")


class SubdomainTemplateListingSerializer(serializers.ModelSerializer):
    """
    SubdomainTemplateListingSerializer
    """
    event_name = serializers.CharField(source="event.event_name", read_only=True, default="")
    event_slug = serializers.CharField(source="event.slug", read_only=True, default="")
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    domain = serializers.CharField(source="site.domain_name", read_only=True, default="")

    class Meta:
        model = NotificationTemplate
        fields = ("id", "status_name", "domain", "event_name", "event_slug", "status", "email_subject", "added_on")


class SubdomainTemplateDetailSerializer(serializers.ModelSerializer):
    """
    SubdomainTemplateDetailSerializer
    """

    class Meta:
        model = NotificationTemplate
        fields = ("id", "site_id", "event_id", "email_subject", "email_content", "notification_text",
                  "push_notification_text", "status")


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    NotificationDetailSerializer
    """
    # profile_image = serializers.SerializerMethodField()

    class Meta:
        model = EventNotification
        fields = ("id", "title", "content", "added_on", "redirect_url")

    @staticmethod
    def get_profile_image(obj):
        try:
            data = {}
            if obj.added_by.profile_image is not None and int(obj.added_by.profile_image) > 0:
                user_uploads = UserUploads.objects.get(id=int(obj.added_by.profile_image))
                data['doc_file_name'] = user_uploads.doc_file_name
                data['bucket_name'] = user_uploads.bucket_name
            return data
        except Exception as exp:
            return {}


class NotificationListingSerializer(serializers.ModelSerializer):
    """
    NotificationListingSerializer
    """

    class Meta:
        model = EventNotification
        fields = ("id", "title", "content", "added_on", "redirect_url")


class TemplateListSerializer(serializers.ModelSerializer):
    """
    TemplateListSerializer
    """
    event_name = serializers.CharField(source="event.event_name", read_only=True, default="")
    event_slug = serializers.CharField(source="event.slug", read_only=True, default="")

    class Meta:
        model = NotificationTemplate
        fields = ("id", "event_name", "event_slug")     





