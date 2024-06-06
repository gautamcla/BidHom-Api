# -*- coding: utf-8 -*-
"""Users Serializer

"""
from rest_framework import serializers
# from api.users.models import *
# from api.payments.models import *
# from api.property.models import *
from api.bid.models import *
from django.db.models import F


class DetailSerializer(serializers.ModelSerializer):
    """
    DetailSerializer
    """
    banner_images = serializers.SerializerMethodField()
    footer_images = serializers.SerializerMethodField()
    # about_images = serializers.SerializerMethodField()
    custom_site_settings = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    auctions = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    social_account = serializers.SerializerMethodField()
    dashboard_numbers = serializers.SerializerMethodField()
    active_auction = serializers.SerializerMethodField()
    active_expertise = serializers.SerializerMethodField()
    featured_property = serializers.SerializerMethodField()

    class Meta:
        model = NetworkDomain
        fields = ("id", "domain_name", "banner_images", "footer_images", "custom_site_settings",
                  "articles", "auctions", "expertise", "social_account", "dashboard_numbers", "active_auction",
                  "active_expertise", "featured_property")

    @staticmethod
    def get_banner_images(obj):
        try:
                return obj.network_upload_domain.filter(status=1, upload_type=1, upload__is_active=1).values("id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_footer_images(obj):
        try:
            return obj.network_upload_domain.filter(status=1, upload_type=2, upload__is_active=1).values("id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

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
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name,
                                "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                elif i.settings_name == "website_logo":
                    user_uploads = UserUploads.objects.filter(id=int(i.setting_value), is_active=1).first()
                    temp = {}
                    if user_uploads is not None:
                        temp = {"image_name": user_uploads.doc_file_name, "bucket_name": user_uploads.bucket_name,
                                "upload_id": user_uploads.id}
                    all_data[i.settings_name] = temp
                else:
                    all_data[i.settings_name] = i.setting_value
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_articles(obj):
        try:
            return obj.network_articles_domain.filter(status=1).order_by("-id").values("id", "title", "description",
                                                                                       "author_name", "author_image_id",
                                                                                       "added_on", "publish_date",
                                                                                       article_image_id=F("upload"),
                                                                                       image=F("upload__doc_file_name"),
                                                                                       author_image_name=F(
                                                                                           "author_image__doc_file_name"),
                                                                                       article_image_name=F(
                                                                                           "upload__doc_file_name"),
                                                                                       author_image_bucket_name=F(
                                                                                           "author_image__bucket_name"),
                                                                                       article_image_name_bucket_name=F(
                                                                                           "upload__bucket_name"),
                                                                                       category_name=F("asset__name"))[0: 3]
        except Exception as exp:
            return []

    @staticmethod
    def get_auctions(obj):
        try:
            return obj.network_auction_domain.order_by("id").values("id", "auction_name", "upload_id", "status", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_expertise(obj):
        try:
            return obj.network_expertise_domain.order_by("id").values("id", "expertise_name", "upload_id", "status",
                                                                      expertise_icon_type_id=F("expertise_icon__icon_type"),
                                                                      expertise_icon_name=F("expertise_icon__icon_name"),
                                                                      doc_file_name=F("upload__doc_file_name"),
                                                                      bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_social_account(obj):
        try:
            return obj.network_social_account_domain.filter(status=1, url__isnull=False).exclude(url="").order_by("position").values("id", "account_type", "url", "status", "position")
        except Exception as exp:
            return []

    @staticmethod
    def get_dashboard_numbers(obj):
        try:
            return obj.dashboard_numbers_domain.filter(status=1).order_by("id").values("id", "title", "value", "status")
        except Exception as exp:
            return []

    @staticmethod
    def get_active_auction(obj):
        try:
            return obj.network_auction_domain.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_active_expertise(obj):
        try:
            return obj.network_expertise_domain.filter(status=1).count()
        except Exception as exp:
            return 0

    def get_featured_property(self, obj):
        try:
            return FeaturedPropertySerializer(obj.property_listing_domain.filter(is_featured=1, is_approved=1, status=1).order_by("-id")[0: 6], many=True, context=self.context).data
        except Exception as exp:
            return []


class FeaturedPropertySerializer(serializers.ModelSerializer):
    """
    FeaturedPropertySerializer
    """
    property_image = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    property_asset = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    start_price = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    property_current_price = serializers.SerializerMethodField()
    current_best_offer = serializers.SerializerMethodField()
    un_priced = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address", "name", "property_asset", "auction_type", "start_price",
                  "start_date", "end_date", "status", "sale_by_type_id", "status_id", "added_on",
                  "property_current_price", "highest_best_format", "current_best_offer", "un_priced",
                  "highest_best_format", "is_favourite", "idx_property_id", "idx_property_image")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return obj.address_one
        except Exception as exp:
            return ""

    @staticmethod
    def get_name(obj):
        try:
            # name = obj.address_one
            name = obj.city
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_asset(obj):
        try:
            return obj.property_asset.name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_price(obj):
        try:
            return obj.property_auction.first().start_price

        except Exception as exp:
            return 0

    @staticmethod
    def get_start_date(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_end_date(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return 0

    @staticmethod
    def get_property_current_price(obj):
        try:
            bid = obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if obj.sale_by_type_id not in [4, 7] and bid is not None:
                return bid.bid_amount
            else:
                return 0
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_best_offer(obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, status=1).order_by("offer_price").last()
            return offer_data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_un_priced(obj):
        try:
            auction_type = obj.sale_by_type_id
            if int(auction_type) == 7:
                return obj.property_auction.first().un_priced
            else:
                return None
        except Exception as exp:
            return None

    def get_is_favourite(self, obj):
        try:
            user_id = self.context
            if user_id is not None:
                data = obj.property_favourite_property.filter(domain=obj.domain_id, property=obj.id, user=user_id).first()
                if data is not None:
                    return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                data = obj.property_idx_property_uploads.filter(status=1).first()
                all_data = {"id": data.id, "upload": data.upload}
                return all_data
            else:
                return {}
        except Exception as exp:
            return {}

