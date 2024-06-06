# -*- coding: utf-8 -*-
"""Cms Serializer

"""
from rest_framework import serializers
# from api.users.models import *
from api.cms.models import *
from django.db.models import F


class CmsContentSerializer(serializers.ModelSerializer):
    """
    CmsContentSerializer
    """
    class Meta:
        model = CmsContent
        fields = '__all__'


class CmsDetailSerializer(serializers.ModelSerializer):
    """
    CmsDetailSerializer
    """
    site_domain = serializers.CharField(source="site.domain_name", read_only=True, default="")

    class Meta:
        model = CmsContent
        fields = ('id', 'site_id', 'page_title', 'meta_key_word', 'meta_description', 'meta_title', 'page_content',
                  'added_by', 'updated_by', 'status', 'site_domain', 'slug')


class AdminCmsListingSerializer(serializers.ModelSerializer):
    """
    AdminCmsListingSerializer
    """
    site_domain = serializers.CharField(source="site.domain_name", read_only=True, default="")
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = CmsContent
        fields = ('id', 'site_id', 'page_title', 'meta_key_word', 'meta_description', 'meta_title', 'page_content',
                  'added_by', 'updated_by', 'status', 'site_domain', 'slug', 'status_name')


class AdminArticleListingSerializer(serializers.ModelSerializer):
    """
    AdminArticleListingSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    category_name = serializers.CharField(source="asset.name", read_only=True, default="")

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status", "status_name",
                  "added_on", "domain", "domain_name", "publish_date", "category_name")

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


class AdminAddArticleSerializer(serializers.ModelSerializer):
    """
    AdminAddArticleSerializer
    """

    class Meta:
        model = NetworkArticles
        fields = "__all__"


class AdminArticleDetailSerializer(serializers.ModelSerializer):
    """
    AdminArticleDetailSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status", "domain",
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


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    ArticleDetailSerializer
    """
    author_image = serializers.SerializerMethodField()
    article_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="asset.name", read_only=True, default="")

    class Meta:
        model = NetworkArticles
        fields = ("id", "title", "description", "author_name", "author_image", "article_image", "status",
                  "publish_date", "category_name")

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


class AboutProfileSerializer(serializers.ModelSerializer):
    """
    AboutProfileSerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    domain_url = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = UserBusinessProfile
        fields = ("company_name", "email", "phone_no", "mobile_no", "address_first", "state", "postal_code",
                  "domain_url", "address")

    @staticmethod
    def get_domain_url(obj):
        try:
            return obj.user.site.domain_url
        except Exception as exp:
            return ""

    @staticmethod
    def get_address(obj):
        try:
            data = obj.user.profile_address_user.filter(user=obj.user_id, address_type=2, status=1)
            return AddressSerializer(data, many=True).data
        except Exception as exp:
            return []


class AddressSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("id", "address_first", "city", "state", "postal_code")


class SocialAccountSerializer(serializers.ModelSerializer):
    """
    SocialAccountSerializer
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = NetworkSocialAccount
        fields = ("name", "url", "account_type")

    @staticmethod
    def get_name(obj):
        try:
            data = {1: "facebook", 2: "twitter", 3: "youtube", 4: "linkedin", 5: "instagram"}
            return data[obj.account_type]
        except Exception as exp:
            return ""


class SaveContactSerializer(serializers.ModelSerializer):
    """
    SaveContactSerializer
    """

    class Meta:
        model = ContactUs
        fields = "__all__"


class VideoTutorialsSerializer(serializers.ModelSerializer):
    """
    VideoTutorialsSerializer
    """

    class Meta:
        model = VideoTutorials
        fields = ("id", "title", "description", "video_url")


class SuperAdminVideoTutorialsListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminVideoTutorialsListingSerializer
    """
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    status_id = serializers.CharField(source="status.id", read_only=True, default="")

    class Meta:
        model = VideoTutorials
        fields = ("id", "title", "video_url", "added_by", "updated_by", "domain_name", "status", "status_id")


class SuperAdminAddVideoTutorialsSerializer(serializers.ModelSerializer):
    """
    SuperAdminAddVideoTutorialsSerializer
    """

    class Meta:
        model = VideoTutorials
        fields = "__all__"


class SubdomainCmsSerializer(serializers.ModelSerializer):
    """
    SubdomainCmsSerializer
    """

    class Meta:
        model = CmsContent
        fields = "__all__"




