# -*- coding: utf-8 -*-
"""blog Serializer

"""
from rest_framework import serializers
# from api.users.models import *
from api.payments.models import *
from api.property.models import *
from django.db.models import F
from django.utils import timezone


class BlogSidebarSerializer(serializers.ModelSerializer):
    """
    BlogSidebarSerializer
    """
    blog_category = serializers.SerializerMethodField()
    recent_post = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ("blog_category", "recent_post")

    @staticmethod
    def get_blog_category(obj):
        try:
            data = NetworkArticleCategory.objects.filter(status=1).order_by("-id").values("id", "name")
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_recent_post(obj):
        try:
            # min_dt = timezone.now() - timedelta(hours=720)
            max_dt = timezone.now()
            data = NetworkArticles.objects.filter(domain=obj.id, status=1, publish_date__lte=max_dt).order_by("-publish_date")[0: 4]
            return RecentPostSerializer(data, many=True).data
        except Exception as exp:
            return []


class RecentPostSerializer(serializers.ModelSerializer):
    """
    RecentPostSerializer
    """
    article_image = serializers.SerializerMethodField()

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "article_image")

    @staticmethod
    def get_article_image(obj):
        try:
            data = {}
            data['image_name'] = obj.upload.doc_file_name
            data['bucket_name'] = obj.upload.bucket_name
            return data
        except Exception as exp:
            return {}


class FrontArticleListingSerializer(serializers.ModelSerializer):
    """
    FrontArticleListingSerializer
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


class FrontArticleDetailSerializer(serializers.ModelSerializer):
    """
    FrontArticleDetailSerializer
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


class BlogCategorySerializer(serializers.ModelSerializer):
    """
    BlogCategorySerializer
    """
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = NetworkArticleCategory
        fields = ("id", "status", "status_name", "name", "added_on", "updated_on")

