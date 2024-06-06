# -*- coding: utf-8 -*-
"""Faq Serializer

"""
from rest_framework import serializers
from api.bid.models import *
from django.db.models import F
from api.packages.common import *


class BidRegistrationDetailSerializer(serializers.ModelSerializer):
    """
    BidRegistrationDetailSerializer
    """
    address = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    auction_id = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "email", "phone_no", "address", "property", "company_name", "auction_id")

    @staticmethod
    def get_address(obj):
        try:
            return AddressSerializer(obj.profile_address_user.filter(address_type=1, status=1).first()).data
        except Exception as exp:
            return {}

    def get_property(self, obj):
        try:
            property_data = PropertyListing.objects.get(id=int(self.context), status=1)
            return PropertySerializer(property_data).data
        except Exception as exp:
            return {}

    def get_company_name(self, obj):
        try:
            return PropertyListing.objects.get(id=int(self.context), status=1).domain.domain_name
        except Exception as exp:
            return ""

    def get_auction_id(self, obj):
        try:
            return PropertyAuction.objects.filter(property_id=int(self.context)).first().id
        except Exception as exp:
            return ""


class AddressSerializer(serializers.ModelSerializer):
    """
    AddressSerializer
    """
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("address_first", "city", "state", "postal_code", "county", "state_name")


class PropertySerializer(serializers.ModelSerializer):
    """
    PropertySerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_image = serializers.SerializerMethodField()
    is_deposit_required = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("address_one", "city", "state", "postal_code", "property_image", "property_asset", "is_deposit_required", "deposit_amount")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_deposit_required(obj):
        try:
            users = Users.objects.filter(site=obj.domain_id, status=1).last()
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0, status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0, is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1, is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1, is_agent=0, status=1, is_deposit_required=1).last()

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
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0, status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0, is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1, is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1, is_agent=0, status=1, is_deposit_required=1).last()

            if data is not None and data.is_deposit_required:
                return int(data.deposit_amount)
            else:
                return ""
        except Exception as exp:
            return ""        


class SubdomainBidRegistrationListingSerializer(serializers.ModelSerializer):
    """
    SubdomainBidRegistrationListingSerializer
    """
    registrant = serializers.SerializerMethodField()
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    email = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    ip_address = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    is_approved_id = serializers.IntegerField(source="is_approved", read_only=True, default="")
    auction_id = serializers.SerializerMethodField()
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    bid_count = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "registrant", "company", "email", "is_reviewed", "is_approved", "added_on", "updated_on",
                  "property_address_one", "property_city", "property_state", "property_postal_code", "ip_address",
                  "property_image", "property", "phone_no", "is_approved_id", "user_id", "auction_id", "status_name",
                  "status", "bid_count", "user_type", "auction_type")

    @staticmethod
    def get_registrant(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_email(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_reviewed(obj):
        try:
            return "Reviewed" if int(obj.is_reviewed) == 1 else "Not Reviewed"
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_approved(obj):
        try:
            approval = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
            return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_ip_address(obj):
        try:
            return obj.ip_address
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

    @staticmethod
    def get_phone_no(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_count(obj):
        try:
            return Bid.objects.filter(domain=obj.domain_id, property=obj.property_id, user=obj.user_id).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(obj.user_type)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.property.sale_by_type_id
        except Exception as exp:
            return ""


class BidRegistrationSerializer(serializers.ModelSerializer):
    """
    BidRegistrationSerializer
    """

    class Meta:
        model = BidRegistration
        fields = "__all__"


class SubdomainBidRegistrationDetailSerializer(serializers.ModelSerializer):
    """
    SubdomainBidRegistrationDetailSerializer
    """
    buyer_information = serializers.SerializerMethodField()
    agent_information = serializers.SerializerMethodField()
    buyer_agent_information = serializers.SerializerMethodField()
    registration_information = serializers.SerializerMethodField()
    asset_information = serializers.SerializerMethodField()
    note_information = serializers.SerializerMethodField()
    upload_information = serializers.SerializerMethodField()
    uploads_information = serializers.SerializerMethodField()
    review_information = serializers.SerializerMethodField()
    registration_history = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    property_image = serializers.SerializerMethodField()
    other_user_information = serializers.SerializerMethodField()
    other_agent_information = serializers.SerializerMethodField()
    registered_user_id = serializers.IntegerField(source="user_id", read_only=True, default="")
    auction_id = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "buyer_information", "registration_information", "asset_information", "note_information",
                  "upload_information", "review_information", "registration_history", "property_address_one",
                  "property_city", "property_state", "property_postal_code", "property_image", "property",
                  "working_with_agent", "property_yourself", "user_type", "other_user_information",
                  "other_agent_information", "agent_information", "buyer_agent_information", "uploads_information",
                  "upload_pof", "registered_user_id", "auction_id", "auction_type")

    @staticmethod
    def get_buyer_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=2).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_agent_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=1).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_buyer_agent_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=3).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_registration_information(obj):
        try:
            data = {}
            data['added_on'] = obj.added_on
            data['updated_on'] = obj.updated_on
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type_id'] = obj.user_type
            data['user_type'] = user_type[obj.user_type]
            data['working_with_agent'] = obj.working_with_agent
            data['property_yourself'] = obj.property_yourself
            data['is_document_vault'] = obj.property.document_vault_visit_property.filter(user=obj.user_id, domain=obj.domain_id).count()
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asset_information(obj):
        try:
            data = {}
            data['asset_name'] = obj.property.property_asset.name
            data['property_type'] = obj.property.property_type.property_type
            data['address_one'] = obj.property.address_one
            data['city'] = obj.property.city
            data['state'] = obj.property.state.state_name
            data['postal_code'] = obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_note_information(obj):
        try:
            data = {}
            data['buyer_comment'] = obj.buyer_comment
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_upload_information(obj):
        try:
            return obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_uploads_information(obj):
        try:
            data = {}
            reason_for_not_upload = {1: "Currently Working With My Lender To Obtain Financing", 2: "Put Me In Contact With Lender(s) To Obtain Financing", 3: "Request Listing Agent Approval, Based On Our Working Relationship"}
            data['pof_upload'] = obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            data['reason_for_not_upload'] = reason_for_not_upload[obj.reason_for_not_upload] if obj.reason_for_not_upload is not None else ""
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_review_information(obj):
        try:
            data = {}
            data['is_reviewed'] = 1 if obj.is_reviewed else 0
            data['is_approved'] = obj.is_approved
            data['seller_comment'] = obj.seller_comment
            approval_data = obj.bid_limit_registration.filter(status=1).last()
            data['approval_limit'] = approval_data.approval_limit if approval_data is not None else ""
            return data
        except Exception as exp:
            print(exp)
            return {}

    @staticmethod
    def get_registration_history(obj):
        try:
            return RegistrationHistorySerializer(obj.bid_limit_registration.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_user_information(obj):
        try:
            data = {}
            if obj.user_type == 4 and obj.property_yourself != 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=2, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_agent_information(obj):
        try:
            data = {}
            if obj.user_type == 2 and obj.working_with_agent == 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=1, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.property.sale_by_type_id
        except Exception as exp:
            return ""


class RegistrationHistorySerializer(serializers.ModelSerializer):
    """
    RegistrationHistorySerializer
    """
    is_approved = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="registration.property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="registration.property.city", read_only=True, default="")
    property_state = serializers.CharField(source="registration.property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="registration.property.postal_code", read_only=True, default="")
    seller_comment = serializers.CharField(source="registration.seller_comment", read_only=True, default="")
    is_approved_id = serializers.IntegerField(source="registration.is_approved", read_only=True, default="")

    class Meta:
        model = BidLimit
        fields = ("id", "registration", "approval_limit", "is_approved", "added_on", "updated_on",
                  "property_address_one", "property_city", "property_state", "property_postal_code", "seller_comment",
                  "is_approved_id")

    @staticmethod
    def get_is_approved(obj):
        try:
            approval_type = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
            return approval_type[obj.is_approved]
        except Exception as exp:
            return ""


class SuperAdminBidRegistrationListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminBidRegistrationListingSerializer
    """
    registrant = serializers.SerializerMethodField()
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    email = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    ip_address = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    auction_id = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    status_name = serializers.CharField(source="status.status_name", read_only=True, default="")
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "registrant", "user_id", "property_id", "auction_id", "bid_count",  "company", "email", "is_reviewed", "is_approved", "added_on", "updated_on",
                  "property_address_one", "property_city", "property_state", "property_postal_code", "ip_address",
                  "phone_no", "status_name", "status", "user_type")

    @staticmethod
    def get_user_type(obj):
        try:
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(obj.user_type)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""
    
    @staticmethod
    def get_bid_count(obj):
        try:
            return Bid.objects.filter(domain=obj.domain_id, property=obj.property_id, user=obj.user_id).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_registrant(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_reviewed(obj):
        try:
            return "Reviewed" if int(obj.is_reviewed) == 1 else "Not Reviewed"
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_approved(obj):
        try:
            approval = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
            return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_ip_address(obj):
        try:
            return obj.ip_address
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3).first()
            else:
                data = data.filter(address_type=2).first()
            return data.phone_no
        except Exception as exp:
            return ""


class SuperAdminBidRegistrationDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminBidRegistrationDetailSerializer
    """
    buyer_information = serializers.SerializerMethodField()
    registration_information = serializers.SerializerMethodField()
    asset_information = serializers.SerializerMethodField()
    note_information = serializers.SerializerMethodField()
    upload_information = serializers.SerializerMethodField()
    review_information = serializers.SerializerMethodField()
    registration_history = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    property_image = serializers.SerializerMethodField()
    other_user_information = serializers.SerializerMethodField()
    other_agent_information = serializers.SerializerMethodField()
    uploads_information = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "buyer_information", "registration_information", "asset_information", "note_information",
                  "upload_information", "review_information", "registration_history", "property_address_one",
                  "property_city", "property_state", "property_postal_code", "property_image", "property",
                  "working_with_agent", "property_yourself", "user_type", "other_user_information",
                  "other_agent_information", "uploads_information")

    @staticmethod
    def get_buyer_information(obj):
        try:
            data = {}
            data['first_name'] = obj.user.first_name
            data['last_name'] = obj.user.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = obj.user.email
            data['phone_no'] = obj.user.phone_no
            address = obj.user.profile_address_user.filter(address_type=1, status=1).first()
            data['address_first'] = address.address_first
            data['city'] = address.city
            data['state'] = address.state.state_name
            data['postal_code'] = address.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_registration_information(obj):
        try:
            data = {}
            data['added_on'] = obj.added_on
            data['updated_on'] = obj.updated_on
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type_id'] = obj.user_type
            data['user_type'] = user_type[obj.user_type]
            data['working_with_agent'] = obj.working_with_agent
            data['property_yourself'] = obj.property_yourself
            data['is_document_vault'] = obj.property.document_vault_visit_property.filter(user=obj.user_id, domain=obj.domain_id).count()
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asset_information(obj):
        try:
            data = {}
            data['asset_name'] = obj.property.property_asset.name
            data['property_type'] = obj.property.property_type.property_type
            data['address_one'] = obj.property.address_one
            data['city'] = obj.property.city
            data['state'] = obj.property.state.state_name
            data['postal_code'] = obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_note_information(obj):
        try:
            data = {}
            data['buyer_comment'] = obj.buyer_comment
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_upload_information(obj):
        try:
            return obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []
    

    @staticmethod
    def get_uploads_information(obj):
        try:
            data = {}
            reason_for_not_upload = {1: "Currently Working With My Lender To Obtain Financing", 2: "Put Me In Contact With Lender(s) To Obtain Financing", 3: "Request Listing Agent Approval, Based On Our Working Relationship"}
            data['pof_upload'] = obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            data['reason_for_not_upload'] = reason_for_not_upload[obj.reason_for_not_upload] if obj.reason_for_not_upload is not None else ""
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_review_information(obj):
        try:
            data = {}
            data['is_reviewed'] = 1 if obj.is_reviewed else 0
            data['is_approved'] = obj.is_approved
            data['seller_comment'] = obj.seller_comment
            data['approval_limit'] = obj.bid_limit_registration.filter(status=1).last().approval_limit
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_registration_history(obj):
        try:
            return RegistrationHistorySerializer(obj.bid_limit_registration.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_user_information(obj):
        try:
            data = {}
            if obj.user_type == 4 and obj.property_yourself != 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=2, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['city'] = bid_registration.city
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_agent_information(obj):
        try:
            data = {}
            if obj.user_type == 2 and obj.working_with_agent == 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=1, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['city'] = bid_registration.city
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}


class SuperAdminBidRegistrationDetailNewSerializer(serializers.ModelSerializer):
    """
    SuperAdminBidRegistrationDetailNewSerializer
    """
    buyer_information = serializers.SerializerMethodField()
    agent_information = serializers.SerializerMethodField()
    buyer_agent_information = serializers.SerializerMethodField()
    registration_information = serializers.SerializerMethodField()
    asset_information = serializers.SerializerMethodField()
    note_information = serializers.SerializerMethodField()
    upload_information = serializers.SerializerMethodField()
    uploads_information = serializers.SerializerMethodField()
    review_information = serializers.SerializerMethodField()
    registration_history = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    property_image = serializers.SerializerMethodField()
    other_user_information = serializers.SerializerMethodField()
    other_agent_information = serializers.SerializerMethodField()
    registered_user_id = serializers.IntegerField(source="user_id", read_only=True, default="")
    auction_id = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "buyer_information", "registration_information", "asset_information", "note_information",
                  "upload_information", "review_information", "registration_history", "property_address_one",
                  "property_city", "property_state", "property_postal_code", "property_image", "property",
                  "working_with_agent", "property_yourself", "user_type", "other_user_information",
                  "other_agent_information", "agent_information", "buyer_agent_information", "uploads_information",
                  "upload_pof", "registered_user_id", "auction_id", "auction_type")

    @staticmethod
    def get_buyer_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=2).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_agent_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=1).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_buyer_agent_information(obj):
        try:
            all_data = obj.bid_registration_address_registration.filter(address_type=3).first()
            data = {}
            data['first_name'] = all_data.first_name
            data['last_name'] = all_data.last_name
            data['company_name'] = obj.domain.domain_name
            data['email'] = all_data.email
            data['phone_no'] = all_data.phone_no
            data['address_first'] = all_data.address_first
            data['state'] = all_data.state.state_name
            data['postal_code'] = all_data.postal_code
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type'] = user_type[obj.user_type]
            data['ip_address'] = obj.ip_address
            data['city'] = all_data.city
            data['company_name'] = all_data.company_name
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_registration_information(obj):
        try:
            data = {}
            data['added_on'] = obj.added_on
            data['updated_on'] = obj.updated_on
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            data['user_type_id'] = obj.user_type
            data['user_type'] = user_type[obj.user_type]
            data['working_with_agent'] = obj.working_with_agent
            data['property_yourself'] = obj.property_yourself
            data['is_document_vault'] = obj.property.document_vault_visit_property.filter(user=obj.user_id, domain=obj.domain_id).count()
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asset_information(obj):
        try:
            data = {}
            data['asset_name'] = obj.property.property_asset.name
            data['property_type'] = obj.property.property_type.property_type
            data['address_one'] = obj.property.address_one
            data['city'] = obj.property.city
            data['state'] = obj.property.state.state_name
            data['postal_code'] = obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_note_information(obj):
        try:
            data = {}
            data['buyer_comment'] = obj.buyer_comment
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_upload_information(obj):
        try:
            return obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_uploads_information(obj):
        try:
            data = {}
            reason_for_not_upload = {1: "Currently Working With My Lender To Obtain Financing", 2: "Put Me In Contact With Lender(s) To Obtain Financing", 3: "Request Listing Agent Approval, Based On Our Working Relationship"}
            data['pof_upload'] = obj.proof_funds_registration.filter(status=1).values("upload_id", doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            data['reason_for_not_upload'] = reason_for_not_upload[obj.reason_for_not_upload] if obj.reason_for_not_upload is not None else ""
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_review_information(obj):
        try:
            data = {}
            data['is_reviewed'] = 1 if obj.is_reviewed else 0
            data['is_approved'] = obj.is_approved
            data['seller_comment'] = obj.seller_comment
            approval_data = obj.bid_limit_registration.filter(status=1).last()
            data['approval_limit'] = approval_data.approval_limit if approval_data is not None else ""
            return data
        except Exception as exp:
            print(exp)
            return {}

    @staticmethod
    def get_registration_history(obj):
        try:
            return RegistrationHistorySerializer(obj.bid_limit_registration.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_user_information(obj):
        try:
            data = {}
            if obj.user_type == 4 and obj.property_yourself != 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=2, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_other_agent_information(obj):
        try:
            data = {}
            if obj.user_type == 2 and obj.working_with_agent == 1:
                bid_registration = obj.bid_registration_address_registration.filter(address_type=1, status=1).first()
                data['first_name'] = bid_registration.first_name
                data['last_name'] = bid_registration.last_name
                data['company_name'] = obj.domain.domain_name
                data['email'] = bid_registration.email
                data['phone_no'] = bid_registration.phone_no
                data['address_first'] = bid_registration.address_first
                data['state'] = bid_registration.state.state_name
                data['postal_code'] = bid_registration.postal_code
                user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
                data['user_type'] = user_type[obj.user_type]
                data['ip_address'] = obj.ip_address
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.property.sale_by_type_id
        except Exception as exp:
            return ""


class BidRegistrationAddressSerializer(serializers.ModelSerializer):
    """
    BidRegistrationAddressSerializer
    """

    class Meta:
        model = BidRegistrationAddress
        fields = "__all__"


class BidRegistrationListingSerializer(serializers.ModelSerializer):
    """
    BidRegistrationListingSerializer
    """
    property_image = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    auction_type = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    broker_name = serializers.SerializerMethodField()
    my_bid = serializers.SerializerMethodField()
    current_bid = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    bid_increment = serializers.SerializerMethodField()
    registration_status = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    bid_start_date = serializers.SerializerMethodField()
    bid_end_date = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    auction_id = serializers.SerializerMethodField()
    start_price = serializers.SerializerMethodField()
    next_bid = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    auction_status = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "property_image", "property_address_one", "property_city", "property_state",
                  "property_postal_code", "auction_type", "company", "broker_name", "my_bid", "current_bid",
                  "bid_count", "bid_increment", "registration_status", "is_approved", "bid_start_date",
                  "bid_end_date", "property", "domain_url", "auction_id", "start_price", "next_bid", "approval_status",
                  "auction_status")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_broker_name(obj):
        try:
            data = obj.domain.users_site_id.filter(status=1).first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_my_bid(obj):
        try:
            return obj.property.bid_property.filter(user=obj.user_id, bid_type__in=[2, 3], is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_bid(obj):
        try:
            return obj.property.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_count(obj):
        try:
            return obj.property.bid_property.filter(property=obj.property_id, bid_type__in=[2, 3]).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_increment(obj):
        try:
            return obj.property.property_auction.first().bid_increments
        except Exception as exp:
            return ""

    @staticmethod
    def get_registration_status(obj):
        try:
            approval = {1: "Pending", 2: "Not Reviewed", 3: "Declined", 4: "Not Interested"}
            if obj.is_approved == 2 and obj.is_reviewed:
                return "Approved"
            else:
                return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_approved(obj):
        try:
            if obj.is_approved == 2 and obj.is_reviewed == 1:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bid_start_date(obj):
        try:
            return obj.property.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_end_date(obj):
        try:
            return obj.property.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_price(obj):
        try:
            return obj.property.property_auction.first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_next_bid(obj):
        try:
            auction_data = obj.property.property_auction.last()
            bid_amount = obj.property.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if bid_amount is not None:
                return int(bid_amount.bid_amount) + int(auction_data.bid_increments)
            else:
                return int(auction_data.start_price)
        except Exception as exp:
            return ""

    @staticmethod
    def get_approval_status(obj):
        try:
            if obj.is_approved == 2 and obj.is_reviewed == 1:
                return "Registration Approved But Auction Not Started Yet"
            elif obj.is_approved == 3 or obj.is_approved == 4:
                return "Registration Declined"
            else:
                return "Registration Pending Approval"
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_status(obj):
        try:
            return obj.property.property_auction.first().status_id
        except Exception as exp:
            return ""


class BidPropertyDetailSerializer(serializers.ModelSerializer):
    """
    BidPropertyDetailSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    auction_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    bid_increment = serializers.SerializerMethodField()
    property_type = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "auction_type", "bid_increment", "property_type")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bid_increment(obj):
        try:
            return obj.property_auction.first().bid_increments
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_type(obj):
        try:
            return obj.property_asset.name
        except Exception as exp:
            return ""


class SubdomainBidHistorySerializer(serializers.ModelSerializer):
    """
    SubdomainBidHistorySerializer
    """
    bidder_detail = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "bidder_detail", "bid_amount", "bid_date", "ip_address")

    @staticmethod
    def get_bidder_detail(obj):
        try:
            register = BidRegistration.objects.filter(domain=obj.domain_id, property=obj.property_id, user=obj.user_id).first()
            if not register.property_yourself and register.user_type == 4:
                data = BidRegistrationAddress.objects.filter(registration__user=obj.user_id, registration__property=obj.property_id, address_type=3).first()
            else:
                data = BidRegistrationAddress.objects.filter(registration__user=obj.user_id, registration__property=obj.property_id, address_type=2).first()
            all_data = {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "phone_no": data.phone_no
            }
            return all_data
        except Exception as exp:
            return {}


class NewSubdomainBidHistorySerializer(serializers.ModelSerializer):
    """
    NewSubdomainBidHistorySerializer
    """
    # id = serializers.IntegerField(source="id", read_only=True, default="")
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    start_bid = serializers.SerializerMethodField()
    max_bid = serializers.SerializerMethodField()
    bid_time = serializers.SerializerMethodField()
    bidder_detail = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "user", "bids", "start_bid", "max_bid", "bid_time", "bidder_detail", "domain")

    @staticmethod
    def get_id(obj):
        try:
            print(obj)
            return obj['id']
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj['user']
        except Exception as exp:
            return ""

    @staticmethod
    def get_bids(obj):
        try:
            return obj['bids']
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_bid(obj):
        try:
            return obj['start_bid']
        except Exception as exp:
            return ""

    @staticmethod
    def get_max_bid(obj):
        try:
            return obj['max_bid']
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_time(obj):
        try:
            return obj['bid_time']
        except Exception as exp:
            return ""

    def get_bidder_detail(self, obj):
        try:
            data = BidRegistrationAddress.objects.filter(registration__user=int(obj['user']), registration__property=int(self.context), address_type__in=[2, 3], status=1).first()
            all_data = {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "address_first": data.address_first,
                "city": data.city,
                "state": data.state.iso_name,
                "postal_code": data.postal_code,
                "email": data.email,
                "phone_no": data.phone_no,
                "register_id": data.registration.registration_id,
                "ip_address": data.registration.ip_address
            }
            return all_data
        except Exception as exp:
            return {}


class BidHistorySerializer(serializers.ModelSerializer):
    """
    BidHistorySerializer
    """
    bidder = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    high_bids = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        # model = BidRegistration
        model = Bid
        fields = ("user_id", "bidder", "bids", "high_bids", "date")

    def get_bidder(self, obj):
        try:
            return BidRegistration.objects.get(user_id=int(obj.user_id), property=self.context, status=1).registration_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_bids(obj):
        try:
            return obj.bids
        except Exception as exp:
            return ""

    @staticmethod
    def get_high_bids(obj):
        try:
            return obj.high_bids
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            return obj.bid_date
        except Exception as exp:
            return ""


class AuctionBiddersSerializer(serializers.ModelSerializer):
    """
    AuctionBiddersSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "domain")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class AuctionRegisterSerializer(serializers.ModelSerializer):
    """
    AuctionRegisterSerializer
    """
    bidder_detail = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    bid_limit = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    ca_signed = serializers.SerializerMethodField()
    approval_date = serializers.DateTimeField(source="updated_on", read_only=True, default="")

    class Meta:
        model = BidRegistration
        fields = ("id", "bidder_detail", "company_name", "bid_limit", "approval_status", "ca_signed", "approval_date", "domain")

    @staticmethod
    def get_bidder_detail(obj):
        try:
            data = obj.bid_registration_address_registration
            if obj.user_type == 4 and obj.property_yourself == 0:
                data = data.filter(address_type=3, status=1).first()
            else:
                data = data.filter(address_type=2, status=1).first()
            all_data = {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "phone_no": data.phone_no
            }
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bid_limit(obj):
        try:
            return obj.bid_limit_registration.filter(is_approved=2, status=1).last().approval_limit
        except Exception as exp:
            return ""

    @staticmethod
    def get_approval_status(obj):
        try:
            approval = {1: "Pending", 2: "Not Reviewed", 3: "Declined", 4: "Not Interested"}
            if obj.is_approved == 2 and obj.is_reviewed:
                return "Approved"
            else:
                return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""
        # try:
        #     if obj.is_approved == 2 and obj.is_reviewed == 1:
        #         return "Approved"
        #     elif obj.is_approved == 1:
        #         return "Pending"
        #     else:
        #         return "Declined"
        # except Exception as exp:
        #     return ""

    @staticmethod
    def get_ca_signed(obj):
        try:
            data = obj.property.document_vault_visit_property.filter(user=obj.user_id, domain=obj.domain_id).count()
            return "Yes" if data > 0 else "No"
        except Exception as exp:
            return "No"


class AuctionTotalBidsSerializer(serializers.ModelSerializer):
    """
    AuctionTotalBidsSerializer
    """
    # id = serializers.IntegerField(source="id", read_only=True, default="")
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    start_bid = serializers.SerializerMethodField()
    max_bid = serializers.SerializerMethodField()
    bid_time = serializers.SerializerMethodField()
    bidder_detail = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "user", "bids", "start_bid", "max_bid", "bid_time", "bidder_detail", "domain")

    @staticmethod
    def get_id(obj):
        try:
            print(obj)
            return obj['id']
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj['user']
        except Exception as exp:
            return ""

    @staticmethod
    def get_bids(obj):
        try:
            return obj['bids']
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_bid(obj):
        try:
            return obj['start_bid']
        except Exception as exp:
            return ""

    @staticmethod
    def get_max_bid(obj):
        try:
            return obj['max_bid']
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_time(obj):
        try:
            return obj['bid_time']
        except Exception as exp:
            return ""

    def get_bidder_detail(self, obj):
        try:
            data = BidRegistrationAddress.objects.filter(registration__user=int(obj['user']), registration__property=int(self.context), address_type__in=[2, 3], status=1).first()
            all_data = {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "address_first": data.address_first,
                "city": data.city,
                "state": data.state.iso_name,
                "postal_code": data.postal_code,
                "email": data.email,
                "phone_no": data.phone_no,
                "register_id": data.registration.registration_id,
                "ip_address": data.registration.ip_address
            }
            return all_data
        except Exception as exp:
            return {}


class AuctionTotalWatchingSerializer(serializers.ModelSerializer):
    """
    AuctionTotalWatchingSerializer
    """

    watcher_detail = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "watcher_detail")

    @staticmethod
    def get_watcher_detail(obj):
        try:
            data = obj.user.profile_address_user.filter(user=obj.user_id, status=1).first()
            registration_detail = obj.user.bid_registration_user.filter(property=obj.property_id, status=1).first()
            all_data = {
                "first_name": obj.user.first_name,
                "last_name": obj.user.last_name,
                "address_first": data.address_first,
                "city": data.city,
                "state": data.state.iso_name,
                "postal_code": data.postal_code,
                "email": obj.user.email,
                "phone_no": obj.user.phone_no,
                "register_id": registration_detail.registration_id if registration_detail is not None else "",
                "ip_address": registration_detail.ip_address if registration_detail is not None else ""
            }
            return all_data
        except Exception as exp:
            return {}


class BuyerOfferDetailSerializer(serializers.ModelSerializer):
    """
    BuyerOfferDetailSerializer
    """

    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    user_type = serializers.IntegerField(source="master_offer.user_type", read_only=True, default="2")
    working_with_agent = serializers.BooleanField(source="master_offer.working_with_agent", read_only=True,
                                                      default="None")
    property_in_person = serializers.IntegerField(source="master_offer.property_in_person", read_only=True, default="1")
    pre_qualified_lender = serializers.IntegerField(source="master_offer.pre_qualified_lender", read_only=True,
                                                    default="1")
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    is_accept_visible = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user", "can_action",
                  "master_offer", "property", "is_rejected", "user_type", "working_with_agent", "property_in_person",
                  "pre_qualified_lender", "document", "asking_price", "is_sold", "is_accepted", "is_rejected",
                  "is_accept_visible", "can_accept", "can_counter", "can_reject", "offer_detail")

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.master_offer_id).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return BuyerOfferHistoryDetailSerializer(NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id).last()
                if last_negotiated_offers.offer_by == 2 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.master_offer.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.master_offer.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_accept_visible(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, offer_by=2, status=1).count()
            return True if int(negotiated_offers) > 0 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 2 and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                offer_detail = OfferDetail.objects.filter(master_offer=obj.master_offer_id).first()
                data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                data['closing_period'] = closing_period[offer_detail.closing_period]
                data['financing'] = financing[offer_detail.financing]
                data['offer_contingent'] = offer_detail.offer_contingent
                data['sale_contingency'] = offer_detail.sale_contingency
                data['down_payment'] = offer_detail.down_payment
                data['appraisal_contingent'] = offer_detail.appraisal_contingent
                data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}


class BuyerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    BuyerOfferHistoryDetailSerializer
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    status = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "offer_by")

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


class SellerOfferListingSerializer(serializers.ModelSerializer):
    """
    SellerOfferListingSerializer
    """
    buyer = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "buyer", "offer_price", "date", "property", "document")

    @staticmethod
    def get_buyer(obj):
        try:
            if obj.property.sale_by_type_id == 4:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data = {}
                all_data['first_name'] = data.user.first_name
                all_data['last_name'] = data.user.last_name
                all_data['email'] = data.user.email
                all_data['id'] = data.user_id
            else:
                data = obj.offer_address_master_offer.filter(status=1).last()
                all_data = {}
                all_data['first_name'] = data.first_name
                all_data['last_name'] = data.last_name
                all_data['email'] = data.email
                all_data['id'] = obj.user_id
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            if data is not None:
                return data.added_on
            else:
                return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.document.doc_file_name
            # data['bucket_name'] = obj.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0


class SellerOfferDetailSerializer(serializers.ModelSerializer):
    """
    SellerOfferDetailSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    user_type = serializers.IntegerField(source="master_offer.user_type", read_only=True, default="2")
    working_with_agent = serializers.BooleanField(source="master_offer.working_with_agent", read_only=True, default="None")
    property_in_person = serializers.IntegerField(source="master_offer.property_in_person", read_only=True, default="1")
    pre_qualified_lender = serializers.IntegerField(source="master_offer.pre_qualified_lender", read_only=True, default="1")
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    buyer_id = serializers.IntegerField(source="master_offer.user_id", read_only=True, default="")
    winning_amount = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_detail",
                  "buyer_id", "winning_amount")

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.master_offer_id).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return SellerOfferHistoryDetailSerializer(NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.master_offer.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.master_offer.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                offer_detail = OfferDetail.objects.filter(master_offer=obj.master_offer_id).first()
                if offer_detail is not None:
                    data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                    data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                    data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                    data['closing_period'] = closing_period[offer_detail.closing_period]
                    data['financing'] = financing[offer_detail.financing]
                    data['offer_contingent'] = offer_detail.offer_contingent
                    data['sale_contingency'] = offer_detail.sale_contingency
                    data['down_payment'] = offer_detail.down_payment
                    data['appraisal_contingent'] = offer_detail.appraisal_contingent
                    data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_winning_amount(obj):
        try:
            data = PropertyListing.objects.filter(id=obj.property_id, winner__gt=1, date_sold__isnull=False).first()
            if data is not None and data.sold_price > 0:
                return data.sold_price
            else:
                return 0
        except Exception as exp:
            return 0


class SellerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    SellerOfferHistoryDetailSerializer
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    status = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments")

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


class OfferPropertyDetailSerializer(serializers.ModelSerializer):
    """
    OfferPropertyDetailSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    sale_by_type_name = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "domain", "sale_by_type",
                  "sale_by_type_name")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    OfferDetailSerializer
    """
    address = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "email", "phone_no", "address")

    @staticmethod
    def get_address(obj):
        try:
            return BestFinalAddressSerializer(obj.profile_address_user.filter(address_type=1, status=1).first()).data
        except Exception as exp:
            return {}


class MyOfferListingSerializer(serializers.ModelSerializer):
    """
    MyOfferListingSerializer
    """
    property_image = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    auction_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    asking_price = serializers.SerializerMethodField()
    your_max_offer = serializers.SerializerMethodField()
    offer_status = serializers.SerializerMethodField()
    offer_by = serializers.SerializerMethodField()
    property_status = serializers.CharField(source="status.status_name", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "property_image", "domain_url", "auction_type",
                  "asking_price", "your_max_offer", "offer_status", "offer_by", "property_status")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asking_price(obj):
        try:
            return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_your_max_offer(self, obj):
        try:
            return obj.negotiated_offers_property.filter(user=int(self.context), master_offer__user=self.context, status=1).last().offer_price
        except Exception as exp:
            return ""

    def get_offer_status(self, obj):
        try:
            data = obj.master_offer_property.filter(user=self.context).last()
            display_status = {1: "Offer Pending", 2: "Counter Offer By Seller"}
            if data.accepted_by is not None:
                return "Offer Accepted" if data.accepted_by_id == data.user_id else "Offer Accepted by seller"
            elif obj.status_id != 1:
                return "Sold"
            elif data.is_declined:
                return "Offer Rejected" if data.declined_by_id == data.user_id else "Offer Rejected by seller"
            else:
                data = obj.negotiated_offers_property.filter(master_offer__user=self.context, status=1).last()
                return display_status[data.display_status]
        except Exception as exp:
            return ""

    def get_offer_by(self, obj):
        try:
            return obj.negotiated_offers_property.filter(master_offer__user=self.context, status=1).last().offer_by
        except Exception as exp:
            return ""


class BestOfferListingSerializer(serializers.ModelSerializer):
    """
    BestOfferListingSerializer
    """
    property_image = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    auction_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    asking_price = serializers.SerializerMethodField()
    offer_status = serializers.SerializerMethodField()
    your_offer_price = serializers.SerializerMethodField()
    max_offer_price = serializers.SerializerMethodField()
    user_data = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "property_image", "domain_url", "auction_type",
                  "asking_price", "offer_status", "your_offer_price", "max_offer_price", "user_data",
                  "earnest_deposit_type", "offer_history", "can_accept", "can_counter", "can_reject", "status",
                  "auction_data")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asking_price(obj):
        try:
            return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_offer_status(self, obj):
        try:
            data = obj.master_offer_property.filter(user=self.context).last()
            display_status = {1: "Offer Pending", 2: "Counter Offer By Seller"}
            if data.accepted_by is not None:
                return "Offer Accepted" if data.accepted_by_id == data.user_id else "Offer Accepted by seller"
            elif obj.status_id != 1:
                return "Sold"
            elif data.is_declined:
                return "Offer Rejected" if data.declined_by_id == data.user_id else "Offer Rejected by seller"
            else:
                data = obj.negotiated_offers_property.filter(master_offer__user=self.context, status=1).last()
                return display_status[data.display_status]
        except Exception as exp:
            return ""

    def get_your_offer_price(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            return obj.negotiated_offers_property.filter(master_offer=master_offer.id, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_max_offer_price(obj):
        try:
            return obj.negotiated_offers_property.last().offer_price
        except Exception as exp:
            return ""

    def get_user_data(self, obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            offer_address = OfferAddress.objects.filter(master_offer__user=self.context, master_offer__property=obj.id).first()
            offer_detail = OfferDetail.objects.filter(master_offer__user=self.context, master_offer__property=obj.id).first()
            data['first_name'] = offer_address.first_name if offer_address is not None else ""
            data['last_name'] = offer_address.last_name if offer_address is not None else ""
            data['email'] = offer_address.email if offer_address is not None else ""
            data['address_first'] = offer_address.address_first if offer_address is not None else ""
            data['city'] = offer_address.city if offer_address is not None else ""
            data['state'] = offer_address.state.state_name if offer_address is not None else ""
            data['phone_no'] = offer_address.phone_no if offer_address is not None else ""
            data['postal_code'] = offer_address.postal_code if offer_address is not None else ""
            data['buyer_first_name'] = offer_address.buyer_first_name if offer_address is not None else ""
            data['buyer_last_name'] = offer_address.buyer_last_name if offer_address is not None else ""
            data['buyer_email'] = offer_address.buyer_email if offer_address is not None else ""
            data['buyer_company'] = offer_address.buyer_company if offer_address is not None else ""
            data['buyer_phone_no'] = offer_address.buyer_phone_no if offer_address is not None else ""
            data['user_type'] = offer_address.master_offer.user_type if offer_address is not None else ""
            data['behalf_of_buyer'] = offer_address.master_offer.behalf_of_buyer if offer_address is not None else ""
            data['earnest_money_deposit'] = offer_detail.earnest_money_deposit if offer_detail is not None else ""
            data['due_diligence_period'] = offer_detail.due_diligence_period if offer_detail is not None else ""
            data['closing_period'] = offer_detail.closing_period if offer_detail is not None else ""
            data['negotiation_id'] = offer_detail.master_offer.id if offer_detail is not None else ""
            data['financing'] = financing[offer_detail.financing] if offer_detail is not None else ""
            data['down_payment'] = offer_detail.down_payment if offer_detail is not None else ""
            data['appraisal_contingent'] = offer_detail.appraisal_contingent if offer_detail is not None else ""
            data['closing_cost'] = offer_detail.closing_cost if offer_detail is not None else ""
            data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period] if offer_detail is not None else ""
            data['closing_period'] = closing_period[offer_detail.closing_period] if offer_detail is not None else ""
            data['offer_contingent'] = offer_contingent[offer_detail.offer_contingent] if offer_detail is not None else ""
            data['sale_contingency'] = offer_detail.sale_contingency if offer_detail is not None else ""
            return data
        except Exception as exp:
            return {}

    def get_offer_history(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            return BuyerOfferHistoryDetailSerializer(NegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    def get_can_accept(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if negotiated_offers.offer_by == 2 and obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_can_counter(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_can_reject(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_auction_data(obj):
        try:
            data = {}
            auction = obj.property_auction.first()
            data['start_date'] = auction.start_date
            data['end_date'] = auction.end_date
            return data
        except Exception as exp:
            return {}


class AdminOfferListingSerializer(serializers.ModelSerializer):
    """
    AdminOfferListingSerializer
    """
    buyer = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "buyer", "offer_price", "date", "property", "document")

    @staticmethod
    def get_buyer(obj):
        try:
            data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            all_data = {}
            all_data['first_name'] = data.user.first_name
            all_data['last_name'] = data.user.last_name
            all_data['email'] = data.user.email
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last().added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()

        except Exception as e:
            return 0


class AdminOfferDetailSerializer(serializers.ModelSerializer):
    """
    AdminOfferDetailSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    user_type = serializers.IntegerField(source="master_offer.user_type", read_only=True, default="2")
    working_with_agent = serializers.BooleanField(source="master_offer.working_with_agent", read_only=True, default="None")
    property_in_person = serializers.IntegerField(source="master_offer.property_in_person", read_only=True, default="1")
    pre_qualified_lender = serializers.IntegerField(source="master_offer.pre_qualified_lender", read_only=True, default="1")
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_status = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_status")

    @staticmethod
    def get_document(obj):
        try:
            return obj.master_offer.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0


    @staticmethod
    def get_property_detail(obj):
        try:
            return AdminPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type=4).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.master_offer_id).first()
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return AdminOfferHistoryDetailSerializer(NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.master_offer.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_status(obj):
        try:
            msg = ""
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id == obj.user_id:
                msg = "Offer Accepted by Buyer"
            elif obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id != obj.user_id:
                msg = "Offer Accepted by Seller"
            elif obj.master_offer.property.status_id != 1:
                msg = "Sold"
            elif obj.master_offer.is_declined and obj.master_offer.declined_by_id == obj.user_id:
                msg = "Offer Declined by Buyer"
            elif obj.master_offer.is_declined and obj.master_offer.declined_by_id != obj.user_id:
                msg = "Offer Declined by Seller"
            elif obj.master_offer.user_id == obj.user_id:
                msg = "Offer Pending"
            elif obj.master_offer.user_id != obj.user_id:
                msg = "Counter Offer By Seller"
            return msg
        except Exception as exp:
            return ""


class AdminOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    AdminOfferHistoryDetailSerializer
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    status = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments")

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


class AdminPropertyDetailSerializer(serializers.ModelSerializer):
    """
    AdminPropertyDetailSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "domain")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class BestFinalDetailSerializer(serializers.ModelSerializer):
    """
    BestFinalDetailSerializer
    """
    user_detail = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    is_update = serializers.SerializerMethodField()
    current_offer_detail = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "user_detail", "offer_detail", "documents", "first_name", "last_name", "email", "phone_no", "address",
                  "property", "company_name", "auction_data", "is_update", "current_offer_detail")

    def get_user_detail(self, obj):
        try:
            data = {}
            offer_address = OfferAddress.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).first()
            if offer_address is not None:
                data['first_name'] = offer_address.first_name
                data['last_name'] = offer_address.last_name
                data['email'] = offer_address.email
                data['address_first'] = offer_address.address_first
                data['city'] = offer_address.city
                data['state_id'] = offer_address.state_id
                data['state'] = offer_address.state.state_name
                data['phone_no'] = offer_address.phone_no
                data['postal_code'] = offer_address.postal_code
                data['buyer_first_name'] = offer_address.buyer_first_name
                data['buyer_last_name'] = offer_address.buyer_last_name
                data['buyer_email'] = offer_address.buyer_email
                data['buyer_company'] = offer_address.buyer_company
                data['buyer_phone_no'] = offer_address.buyer_phone_no
            else:
                address = obj.profile_address_user.filter(address_type=1, status=1).first()
                data['first_name'] = obj.first_name
                data['last_name'] = obj.last_name
                data['email'] = obj.email
                data['address_first'] = address.address_first if address is not None else ""
                data['city'] = address.city if address is not None else ""
                data['state_id'] = address.state_id if address is not None else ""
                data['state'] = address.state.state_name if address is not None else ""
                data['phone_no'] = address.phone_no if address is not None else ""
                data['postal_code'] = address.postal_code if address is not None else ""
                data['buyer_first_name'] = ""
                data['buyer_last_name'] = ""
                data['buyer_email'] = ""
                data['buyer_company'] = ""
                data['buyer_phone_no'] = ""
            return data
        except Exception as exp:
            return {}

    def get_offer_detail(self, obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            offer_detail = OfferDetail.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).first()
            if offer_detail is not None:
                data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                data['closing_period'] = closing_period[offer_detail.closing_period]
                data['financing'] = financing[offer_detail.financing]
                data['due_diligence_period_id'] = offer_detail.due_diligence_period
                data['closing_period_id'] = offer_detail.closing_period
                data['financing_id'] = offer_detail.financing
                data['offer_contingent'] = offer_detail.offer_contingent
                data['sale_contingency'] = offer_detail.sale_contingency
                # data['user_type'] = offer_detail.master_offer.user_type
                # data['working_with_agent'] = offer_detail.master_offer.working_with_agent
                # data['property_in_person'] = offer_detail.master_offer.property_in_person
                # data['pre_qualified_lender'] = offer_detail.master_offer.pre_qualified_lender
                # data['step'] = offer_detail.master_offer.steps
                data['down_payment'] = offer_detail.down_payment
                data['appraisal_contingent'] = offer_detail.appraisal_contingent
                data['closing_cost'] = offer_detail.closing_cost
            master_offer = MasterOffer.objects.filter(property=self.context, user=obj.id).first()
            if master_offer is not None:
                data['user_type'] = master_offer.user_type
                data['working_with_agent'] = master_offer.working_with_agent
                data['property_in_person'] = master_offer.property_in_person
                data['pre_qualified_lender'] = master_offer.pre_qualified_lender
                data['step'] = master_offer.steps
                data['document_comment'] = master_offer.document_comment
                data['behalf_of_buyer'] = master_offer.behalf_of_buyer
                offer_amount = master_offer.negotiated_offers_master_offer.filter(user=obj.id, offer_by=1, status=1).last()
                data['current_offer_price'] = offer_amount.offer_price if offer_amount is not None else ""
            current_offer_detail = {}
            current_highest_amount = master_offer.negotiated_offers_master_offer.filter(best_offer_is_accept=1, status=1).order_by("offer_price").last()
            if current_highest_amount is not None:
                current_offer_detail['current_offer_amount'] = current_highest_amount.offer_price if current_highest_amount is not None else ""
                current_highest_detail = master_offer.offer_detail_master_offer.filter(master_offer=current_highest_amount.master_offer_id, status=1).last()
                current_offer_detail['financing'] = financing[current_highest_detail.financing]
                current_offer_detail['down_payment'] = current_highest_detail.down_payment
                current_offer_detail['offer_contingent'] = offer_contingent[current_highest_detail.offer_contingent]
                current_offer_detail['appraisal_contingent'] = current_highest_detail.appraisal_contingent
                current_offer_detail['sale_contingency'] = current_highest_detail.sale_contingency
                current_offer_detail['closing_period'] = closing_period[current_highest_detail.closing_period]
                current_offer_detail['closing_cost'] = current_highest_detail.closing_cost
            data['current_offer_detail'] = current_offer_detail
            return data
        except Exception as exp:
            return {}

    def get_documents(self, obj):
        try:
            offer_documents = OfferDocuments.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).values("id", "document_id", doc_file_name=F("document__doc_file_name"), bucket_name=F("document__bucket_name"))
            return offer_documents
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return BestFinalAddressSerializer(obj.profile_address_user.filter(address_type=1, status=1).first()).data
        except Exception as exp:
            return {}

    def get_property(self, obj):
        try:
            property_data = PropertyListing.objects.get(id=int(self.context))
            return BestFinalPropertySerializer(property_data).data
        except Exception as exp:
            return {}

    def get_company_name(self, obj):
        try:
            return PropertyListing.objects.get(id=int(self.context), status=1).domain.domain_name
        except Exception as exp:
            return ""

    def get_auction_data(self, obj):
        try:
            data = {}
            auction_data = PropertyAuction.objects.filter(property_id=int(self.context)).first()
            if auction_data is not None:
                data['id'] = auction_data.id
                data['start_date'] = auction_data.start_date
                data['end_date'] = auction_data.end_date
                data['start_price'] = auction_data.start_price
                data['un_priced'] = auction_data.un_priced
            return data
        except Exception as exp:
            return {}

    def get_is_update(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=self.context, user=obj.id, is_canceled=0, is_declined=0).first()
            return True if master_offer is not None else False
        except Exception as exp:
            return ""

    def get_current_offer_detail(self, obj):
        try:
            current_offer_detail = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.",
                                    3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            current_highest_amount = NegotiatedOffers.objects.filter(property=self.context,best_offer_is_accept=1,status=1).last()

            if current_highest_amount is not None:
                current_offer_detail[
                    'current_offer_amount'] = current_highest_amount.offer_price if current_highest_amount is not None else ""
                current_highest_detail = OfferDetail.objects.filter(
                    master_offer=current_highest_amount.master_offer_id, status=1).last()
                current_offer_detail['earnest_money_deposit'] = current_highest_detail.earnest_money_deposit
                current_offer_detail['financing'] = financing[current_highest_detail.financing]
                current_offer_detail['down_payment'] = current_highest_detail.down_payment
                current_offer_detail['due_diligence_period'] = due_diligence_period[current_highest_detail.due_diligence_period]
                current_offer_detail['offer_contingent'] = offer_contingent[current_highest_detail.offer_contingent]
                current_offer_detail['appraisal_contingent'] = current_highest_detail.appraisal_contingent
                current_offer_detail['sale_contingency'] = current_highest_detail.sale_contingency
                current_offer_detail['closing_period'] = closing_period[current_highest_detail.closing_period]
                current_offer_detail['closing_cost'] = current_highest_detail.closing_cost
            return current_offer_detail
        except Exception as exp:
            print(exp)
            return {}


class BestFinalAddressSerializer(serializers.ModelSerializer):
    """
    BestFinalAddressSerializer
    """
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = ProfileAddress
        fields = ("address_first", "city", "state", "postal_code", "county", "state_name")


class BestFinalPropertySerializer(serializers.ModelSerializer):
    """
    BestFinalPropertySerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("address_one", "city", "state", "postal_code", "property_image", "due_diligence_period",
                  "escrow_period", "earnest_deposit", "earnest_deposit_type", "status", "highest_best_format")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class GetLoiSerializer(serializers.ModelSerializer):
    """
    GetLoiSerializer
    """
    user_detail = serializers.SerializerMethodField()
    property_detail = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "user_detail", "property_detail", "auction_data", "offer_detail", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "behalf_of_buyer",
                  "buyer_detail")

    @staticmethod
    def get_user_detail(obj):
        try:
            data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.id).first()
            data['first_name'] = offer_address.first_name
            data['last_name'] = offer_address.last_name
            data['email'] = offer_address.email
            data['address_first'] = offer_address.address_first
            data['city'] = offer_address.city
            data['state_id'] = offer_address.state_id
            data['state'] = offer_address.state.state_name
            data['phone_no'] = offer_address.phone_no
            data['postal_code'] = offer_address.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_detail(obj):
        try:
            return LoiPropertySerializer(obj.property).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_data(obj):
        try:
            data = {}
            auction_data = PropertyAuction.objects.filter(property=obj.property_id).first()
            data['id'] = auction_data.id
            data['start_date'] = auction_data.start_date
            data['end_date'] = auction_data.end_date
            data['start_price'] = auction_data.start_price
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.id, status=1).last()
            data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
            data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
            data['closing_period'] = closing_period[offer_detail.closing_period]
            data['financing'] = financing[offer_detail.financing]
            data['due_diligence_period_id'] = offer_detail.due_diligence_period
            data['closing_period_id'] = offer_detail.closing_period
            data['financing_id'] = offer_detail.financing
            data['offer_contingent'] = offer_detail.offer_contingent
            data['sale_contingency'] = offer_detail.sale_contingency
            data['last_offer_price'] = offer_detail.offer_price
            data['down_payment'] = offer_detail.down_payment
            data['appraisal_contingency'] = offer_detail.appraisal_contingent
            data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            if obj.behalf_of_buyer == 1:
                offer_address = OfferAddress.objects.filter(master_offer=obj.id).first()
                data['first_name'] = offer_address.buyer_first_name
                data['last_name'] = offer_address.buyer_last_name
                data['email'] = offer_address.buyer_email
                data['phone_no'] = offer_address.buyer_phone_no
            return data
        except Exception as exp:
            return {}


class LoiPropertySerializer(serializers.ModelSerializer):
    """
    LoiPropertySerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "property_image", "earnest_deposit_type")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}


class SendLoiSerializer(serializers.ModelSerializer):
    """
    SendLoiSerializer
    """
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    user_phone_no = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    agent_first_name = serializers.SerializerMethodField()
    agent_last_name = serializers.SerializerMethodField()
    agent_phone_no = serializers.SerializerMethodField()
    agent_email = serializers.SerializerMethodField()
    user_address_one = serializers.SerializerMethodField()
    user_city = serializers.SerializerMethodField()
    user_state = serializers.SerializerMethodField()
    user_postal_code = serializers.SerializerMethodField()
    property_address_one = serializers.SerializerMethodField()
    property_city = serializers.SerializerMethodField()
    property_state = serializers.SerializerMethodField()
    property_postal_code = serializers.SerializerMethodField()
    start_price = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    financing = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    earnest_money_deposit = serializers.SerializerMethodField()
    down_payment = serializers.SerializerMethodField()
    loan_type = serializers.SerializerMethodField()
    appraisal_contingency = serializers.SerializerMethodField()
    property_sale_contingency = serializers.SerializerMethodField()
    closing_cost = serializers.SerializerMethodField()
    agent_text = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "user_first_name", "user_last_name", "user_phone_no", "user_email", "user_address_one",
                  "user_city", "user_state", "user_postal_code", "property_address_one", "property_city",
                  "property_state", "property_postal_code", "start_price", "due_diligence_period", "closing_period",
                  "financing", "offer_contingent", "earnest_money_deposit", "down_payment", "loan_type",
                  "appraisal_contingency", "property_sale_contingency", "closing_cost", "agent_first_name",
                  "agent_last_name", "agent_phone_no", "agent_email", "agent_text")

    @staticmethod
    def get_user_first_name(obj):
        try:
            data = obj.offer_address_master_offer.first()
            return data.buyer_first_name if obj.behalf_of_buyer == 1 else data.first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_last_name(obj):
        try:
            data = obj.offer_address_master_offer.first()
            return data.buyer_last_name if obj.behalf_of_buyer == 1 else data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_phone_no(obj):
        try:
            data = obj.offer_address_master_offer.first()
            # return data.buyer_phone_no if obj.behalf_of_buyer == 1 else data.phone_no
            phone_number = str(data.buyer_phone_no) if obj.behalf_of_buyer == 1 else (data.phone_no)
            complete_phone = "(" + phone_number[0: 3] + ") " + phone_number[3: 6] + "-" + phone_number[6::]
            return complete_phone
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_email(obj):
        try:
            data = obj.offer_address_master_offer.first()
            return data.buyer_email if obj.behalf_of_buyer == 1 else data.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_agent_first_name(obj):
        try:
            if obj.behalf_of_buyer == 1:
                return obj.offer_address_master_offer.first().first_name
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_agent_last_name(obj):
        try:
            if obj.behalf_of_buyer == 1:
                return obj.offer_address_master_offer.first().last_name
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_agent_phone_no(obj):
        try:
            if obj.behalf_of_buyer == 1:
                # return obj.offer_address_master_offer.first().phone_no
                phone_number = str(obj.offer_address_master_offer.first().phone_no)
                complete_phone = "(" + phone_number[0: 3] + ") " + phone_number[3: 6] + "-" + phone_number[6::]
                return complete_phone
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_agent_email(obj):
        try:
            if obj.behalf_of_buyer == 1:
                return obj.offer_address_master_offer.first().email
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_agent_text(obj):
        try:
            if obj.behalf_of_buyer == 1:
                return "Buyer’s Agent"
            else:
                return ""

        except Exception as exp:
            return ""

    @staticmethod
    def get_user_address_one(obj):
        try:
            return obj.offer_address_master_offer.first().address_first
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_city(obj):
        try:
            return obj.offer_address_master_offer.first().city
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_state(obj):
        try:
            return obj.offer_address_master_offer.first().state.state_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_postal_code(obj):
        try:
            return obj.offer_address_master_offer.first().postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_address_one(obj):
        try:
            return obj.property.address_one
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_city(obj):
        try:
            return obj.property.city
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_state(obj):
        try:
            return obj.property.state.state_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_postal_code(obj):
        try:
            return obj.property.postal_code
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_price(obj):
        try:
            negotiation_offer = obj.highest_best_negotiated_offers_master_offer.filter(status=1, is_declined=0).last()
            # if negotiation_offer is not None:
            #     start_price = int_to_en(negotiation_offer.offer_price).upper() + "($" + str(format(negotiation_offer.offer_price, ",")) + ")"
            # else:
            #     start_price = obj.property.property_auction.first().start_price
            #     start_price = int_to_en(start_price).upper() + "($" + str(format(start_price, ",")) + ")"

            if negotiation_offer is not None:
                start_price = "$" + str(format(negotiation_offer.offer_price, ","))
            else:
                start_price = obj.property.property_auction.first().start_price
                start_price = "$" + str(format(start_price, ","))
            return start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.highest_best_negotiated_offers_master_offer.last().due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.highest_best_negotiated_offers_master_offer.last().closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            # return financing[obj.highest_best_negotiated_offers_master_offer.last().financing]
            financing_data = obj.highest_best_negotiated_offers_master_offer.last()
            if financing_data is not None and int(financing_data.financing) == 6:
                return "Yes"
            else:
                return "No"
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            data = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return data[obj.highest_best_negotiated_offers_master_offer.last().offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_earnest_money_deposit(obj):
        try:
            earnest_money_deposit = obj.highest_best_negotiated_offers_master_offer.last().earnest_money_deposit
            # if obj.property.earnest_deposit_type == 1:
            #     return int_to_en(earnest_money_deposit).upper() + "($" + str(format(earnest_money_deposit, ",")) + ")"
            # else:
            #     return str(earnest_money_deposit)+" %"
            start_price = obj.highest_best_negotiated_offers_master_offer.last().offer_price
            if obj.property.earnest_deposit_type == 1:
                percentage = (earnest_money_deposit * 100) / start_price
                return "$" + str(format(round(earnest_money_deposit, 2), ",")) + " or " + str(round(percentage, 2)) + " %"
            else:
                amount = start_price * (earnest_money_deposit / 100)
                # return str(earnest_money_deposit)+" %"
                return "$" + str(format(round(amount, 2), ",")) + " or " + str(round(earnest_money_deposit, 2)) + " %"
        except Exception as exp:
            return ""

    @staticmethod
    def get_down_payment(obj):
        try:
            down_payment = obj.highest_best_negotiated_offers_master_offer.last().down_payment
            # return int_to_en(down_payment).upper() + "($" + str(format(down_payment, ",")) + ")"
            return "$" + str(format(down_payment, ","))
        except Exception as exp:
            return ""

    @staticmethod
    def get_loan_type(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan",
                         6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan",
                         11: "Conduit/CMBS Loan"}
            return financing[obj.highest_best_negotiated_offers_master_offer.last().financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_appraisal_contingency(obj):
        try:
            appraisal_contingency = obj.highest_best_negotiated_offers_master_offer.last().appraisal_contingent
            return "Yes" if appraisal_contingency is not None and int(appraisal_contingency) == 1 else "No"
        except Exception as exp:
            return "-"

    @staticmethod
    def get_property_sale_contingency(obj):
        try:
            property_sale_contingency = obj.highest_best_negotiated_offers_master_offer.last().sale_contingency
            return "Yes" if property_sale_contingency is not None and int(property_sale_contingency) == 1 else "No"
        except Exception as exp:
            return "-"

    @staticmethod
    def get_closing_cost(obj):
        try:
            closing_cost_data = {1: "Buyer agrees to pay for all loan-related closing costs and half of the transaction closing costs.", 2: " Buyer agrees to pay for all loan-related closing costs and all of the transaction closing costs.", 3: " Seller to pay for all loan-related closing costs and all of the transaction closing costs."}
            closing_cost = obj.highest_best_negotiated_offers_master_offer.last().closing_cost
            return closing_cost_data[closing_cost]
        except Exception as exp:
            return "-"


# ------------------Seller Offer Detail-----------------
class SellerOfferDetailsSerializer(serializers.ModelSerializer):
    """
    SellerOfferDetailsSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    comments = serializers.CharField(read_only=True, default="")
    user = serializers.SerializerMethodField()
    master_offer = serializers.IntegerField(source="id", read_only=True, default="")
    buyer_id = serializers.IntegerField(source="user_id", read_only=True, default="")
    idx_property_id = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_detail",
                  "buyer_id", "idx_property_id", "idx_property_image")

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            print(exp)
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = obj.offer_address_master_offer.filter(status=1).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            all_data['behalf_of_buyer'] = obj.behalf_of_buyer
            all_data['buyer_first_name'] = offer_address.buyer_first_name
            all_data['buyer_last_name'] = offer_address.buyer_last_name
            all_data['buyer_email'] = offer_address.buyer_email
            all_data['buyer_company'] = offer_address.buyer_company
            all_data['buyer_phone_no'] = offer_address.buyer_phone_no
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return SellerOfferHistoryDetailSerializer(obj.negotiated_offers_master_offer.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = obj.negotiated_offers_master_offer.filter(status=1).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.accepted_by_id is not None and obj.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = obj.negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None and obj.negotiated_offers_master_offer.filter(status=1).count():
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                offer_detail = OfferDetail.objects.filter(master_offer=obj.id).first()
                if offer_detail is not None:
                    data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                    data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                    data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                    data['closing_period'] = closing_period[offer_detail.closing_period]
                    data['financing'] = financing[offer_detail.financing]
                    data['offer_contingent'] = offer_detail.offer_contingent
                    data['sale_contingency'] = offer_detail.sale_contingency
                    data['down_payment'] = offer_detail.down_payment
                    data['appraisal_contingent'] = offer_detail.appraisal_contingent
                    data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_idx_property_id(obj):
        try:
            data = PropertyListing.objects.filter(id=obj.property_id).first()
            return data.idx_property_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                data = IdxPropertyUploads.filter(property=obj.property_id, status=1).first()
                all_data = {"id": data.id, "upload": data.upload}
                return all_data
            else:
                return {}
        except Exception as exp:
            return {}


class BestSellerOfferListingSerializer(serializers.ModelSerializer):
    """
    BestSellerOfferListingSerializer
    """
    buyer = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    offer_price_detail = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "buyer", "offer_price", "date", "property", "document", "offer_price_detail")

    @staticmethod
    def get_buyer(obj):
        try:
            if obj.property.sale_by_type_id == 4:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data = {}
                all_data['first_name'] = data.user.first_name
                all_data['last_name'] = data.user.last_name
                all_data['email'] = data.user.email
                all_data['id'] = data.user_id
            else:
                data = obj.offer_address_master_offer.filter(status=1).last()
                all_data = {}
                all_data['first_name'] = data.first_name
                all_data['last_name'] = data.last_name
                all_data['email'] = data.email
                all_data['id'] = obj.user_id
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_price(obj):
        try:
            last_data = obj.negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            return data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            last_data = obj.negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            if data is not None:
                return data.added_on
            else:
                return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.document.doc_file_name
            # data['bucket_name'] = obj.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_offer_price_detail(obj):
        try:
            all_data = {}
            last_data = obj.negotiated_offers_master_offer.filter(status=1).last()
            all_data['best_offer_is_accept'] = last_data.best_offer_is_accept
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                all_data['price'] = last_data.offer_price
            else:
                last_data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data['price'] = last_data.offer_price
            return all_data
        except Exception as exp:
            return {}


# ------------------Best Seller Offer Detail-----------------
class BestSellerOfferDetailsSerializer(serializers.ModelSerializer):
    """
    BestSellerOfferDetailsSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_offer_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    comments = serializers.CharField(read_only=True, default="")
    user = serializers.SerializerMethodField()
    master_offer = serializers.IntegerField(source="id", read_only=True, default="")
    buyer_id = serializers.IntegerField(source="user_id", read_only=True, default="")

    class Meta:
        model = MasterOffer
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_detail",
                  "buyer_id", "can_offer_accept")

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            print(exp)
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = obj.offer_address_master_offer.filter(status=1).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            all_data['behalf_of_buyer'] = obj.behalf_of_buyer
            all_data['buyer_first_name'] = offer_address.buyer_first_name
            all_data['buyer_last_name'] = offer_address.buyer_last_name
            all_data['buyer_email'] = offer_address.buyer_email
            all_data['buyer_company'] = offer_address.buyer_company
            all_data['buyer_phone_no'] = offer_address.buyer_phone_no
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return BestSellerOfferHistoryDetailSerializer(obj.negotiated_offers_master_offer.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = obj.negotiated_offers_master_offer.filter(status=1).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.accepted_by_id is not None and obj.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = obj.negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and not negotiated_offers.best_offer_is_accept and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_offer_accept(obj):
        try:
            negotiated_offers = obj.negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None and obj.negotiated_offers_master_offer.filter(status=1).count():
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                offer_detail = OfferDetail.objects.filter(master_offer=obj.id).first()
                if offer_detail is not None:
                    data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                    data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                    data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                    data['closing_period'] = closing_period[offer_detail.closing_period]
                    data['financing'] = financing[offer_detail.financing]
                    data['offer_contingent'] = offer_detail.offer_contingent
                    data['sale_contingency'] = offer_detail.sale_contingency
                    data['down_payment'] = offer_detail.down_payment
                    data['appraisal_contingent'] = offer_detail.appraisal_contingent
                    data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}


class BestSellerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    BestSellerOfferHistoryDetailSerializer
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    status = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "best_offer_is_accept", "offer_by")

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


class BestBuyerOfferDetailSerializer(serializers.ModelSerializer):
    """
    BestBuyerOfferDetailSerializer
    """

    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    user_type = serializers.IntegerField(source="master_offer.user_type", read_only=True, default="2")
    working_with_agent = serializers.BooleanField(source="master_offer.working_with_agent", read_only=True,
                                                      default="None")
    property_in_person = serializers.IntegerField(source="master_offer.property_in_person", read_only=True, default="1")
    pre_qualified_lender = serializers.IntegerField(source="master_offer.pre_qualified_lender", read_only=True,
                                                    default="1")
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    is_accept_visible = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_offer_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user", "can_action",
                  "master_offer", "property", "is_rejected", "user_type", "working_with_agent", "property_in_person",
                  "pre_qualified_lender", "document", "asking_price", "is_sold", "is_accepted", "is_rejected",
                  "is_accept_visible", "can_accept", "can_counter", "can_reject", "offer_detail", "can_offer_accept")

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.master_offer_id).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return BestBuyerOfferHistoryDetailSerializer(NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id).last()
                if last_negotiated_offers.offer_by == 2 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.master_offer.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.master_offer.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_accept_visible(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, offer_by=2, status=1).count()
            return True if int(negotiated_offers) > 0 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 2 and not negotiated_offers.best_offer_is_accept and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_offer_accept(obj):
        try:
            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 2 and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                offer_detail = OfferDetail.objects.filter(master_offer=obj.master_offer_id).first()
                data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                data['closing_period'] = closing_period[offer_detail.closing_period]
                data['financing'] = financing[offer_detail.financing]
                data['offer_contingent'] = offer_detail.offer_contingent
                data['sale_contingency'] = offer_detail.sale_contingency
                data['down_payment'] = offer_detail.down_payment
                data['appraisal_contingent'] = offer_detail.appraisal_contingent
                data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}


class BestBuyerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    BestBuyerOfferHistoryDetailSerializer
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    status = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "best_offer_is_accept", "offer_by")

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


class BestCurrentOfferSerializer(serializers.ModelSerializer):
    """
    BestCurrentOfferSerializer
    """

    earnest_money_deposit = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    closing_date = serializers.SerializerMethodField()
    earnest_deposit_type = serializers.SerializerMethodField()
    financing = serializers.SerializerMethodField()
    down_payment = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    appraisal_contingent = serializers.SerializerMethodField()
    sale_contingency = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    closing_cost = serializers.SerializerMethodField()

    class Meta:
        model = NegotiatedOffers
        fields = ("id", "offer_price", "earnest_money_deposit", "due_diligence_period", "closing_date",
                  "earnest_deposit_type", "financing", "down_payment", "earnest_money_deposit",
                  "due_diligence_period", "offer_contingent", "appraisal_contingent", "sale_contingency",
                  "closing_period", "closing_cost")

    @staticmethod
    def get_earnest_money_deposit(obj):
        try:
            offer_detail = obj.master_offer.offer_detail_master_offer.first()
            return offer_detail.earnest_money_deposit
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            offer_detail = obj.master_offer.offer_detail_master_offer.first()
            return due_diligence_period[offer_detail.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_date(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            offer_detail = obj.master_offer.offer_detail_master_offer.first()
            return closing_period[offer_detail.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_earnest_deposit_type(obj):
        try:
            return obj.property.earnest_deposit_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.master_offer.offer_detail_master_offer.first().financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_down_payment(obj):
        try:
            return obj.master_offer.offer_detail_master_offer.first().down_payment
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.master_offer.offer_detail_master_offer.first().offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_appraisal_contingent(obj):
        try:
            return obj.master_offer.offer_detail_master_offer.first().appraisal_contingent
        except Exception as exp:
            return ""

    @staticmethod
    def get_sale_contingency(obj):
        try:
            return obj.master_offer.offer_detail_master_offer.first().sale_contingency
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.master_offer.offer_detail_master_offer.first().closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_cost(obj):
        try:
            return obj.master_offer.offer_detail_master_offer.first().closing_cost
        except Exception as exp:
            return ""


class EnhancedBestBuyerOfferDetailSerializer(serializers.ModelSerializer):
    """
    EnhancedBestBuyerOfferDetailSerializer
    """

    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    user_type = serializers.IntegerField(source="master_offer.user_type", read_only=True, default="2")
    working_with_agent = serializers.BooleanField(source="master_offer.working_with_agent", read_only=True,
                                                      default="None")
    property_in_person = serializers.IntegerField(source="master_offer.property_in_person", read_only=True, default="1")
    pre_qualified_lender = serializers.IntegerField(source="master_offer.pre_qualified_lender", read_only=True,
                                                    default="1")
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    is_accept_visible = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_offer_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user", "can_action",
                  "master_offer", "property", "is_rejected", "user_type", "working_with_agent", "property_in_person",
                  "pre_qualified_lender", "document", "asking_price", "is_sold", "is_accepted", "is_rejected",
                  "is_accept_visible", "can_accept", "can_counter", "can_reject", "offer_detail", "can_offer_accept")

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.master_offer_id).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return EnhancedBestBuyerOfferHistoryDetailSerializer(HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id).last()
                if last_negotiated_offers.offer_by == 2 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.master_offer.is_canceled == 1 or obj.master_offer.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.master_offer.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.master_offer.accepted_by_id is not None and obj.master_offer.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.master_offer.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.master_offer.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_accept_visible(obj):
        try:
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, offer_by=2, status=1).count()
            return True if int(negotiated_offers) > 0 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 2 and not negotiated_offers.best_offer_is_accept and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_offer_accept(obj):
        try:
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, status=1).last()
            if negotiated_offers.offer_by == 2 and obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined and obj.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                # offer_detail = OfferDetail.objects.filter(master_offer=obj.master_offer_id).first()
                offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.master_offer_id, offer_by=1, status=1).last()
                data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                data['closing_period'] = closing_period[offer_detail.closing_period]
                data['financing'] = financing[offer_detail.financing]
                data['offer_contingent'] = offer_detail.offer_contingent
                data['sale_contingency'] = offer_detail.sale_contingency
                data['down_payment'] = offer_detail.down_payment
                data['appraisal_contingent'] = offer_detail.appraisal_contingent
                data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}


class EnhancedBestBuyerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    EnhancedBestBuyerOfferHistoryDetailSerializer
    """

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "best_offer_is_accept", "offer_by", "is_declined", "property")

    @staticmethod
    def get_first_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.first_name
            else:
                return obj.master_offer.offer_address_master_offer.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.last_name
            else:
                return obj.master_offer.offer_address_master_offer.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer", 4: "Offer Declined"}
            return status[obj.display_status]
        except Exception as exp:
            return ""


# ----------------BestSellerOfferListingSerializer------------------
class EnhancedBestSellerOfferListingSerializer(serializers.ModelSerializer):
    """
    BestSellerOfferListingSerializer
    """
    buyer = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    offer_price_detail = serializers.SerializerMethodField()
    highest_offer_user = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "buyer", "offer_price", "date", "property", "document", "offer_price_detail", "is_declined", "highest_offer_user")

    @staticmethod
    def get_buyer(obj):
        try:
            if obj.property.sale_by_type_id == 4:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data = {}
                all_data['first_name'] = data.user.first_name
                all_data['last_name'] = data.user.last_name
                all_data['email'] = data.user.email
                all_data['id'] = data.user_id
            else:
                data = obj.offer_address_master_offer.filter(status=1).last()
                all_data = {}
                all_data['first_name'] = data.first_name
                all_data['last_name'] = data.last_name
                all_data['email'] = data.email
                all_data['id'] = obj.user_id
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_price(obj):
        try:
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            return data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            if data is not None:
                return data.added_on
            else:
                return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.document.doc_file_name
            # data['bucket_name'] = obj.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_offer_price_detail(obj):
        try:
            all_data = {}
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            all_data['best_offer_is_accept'] = last_data.best_offer_is_accept
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                all_data['price'] = last_data.offer_price
            else:
                last_data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data['price'] = last_data.offer_price
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_highest_offer_user(obj):
        try:
            highest_offer = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.property_id, best_offer_is_accept=1, is_declined=0, master_offer__is_declined=0).order_by("offer_price").last()
            return highest_offer.master_offer.user_id
        except Exception as exp:
            return ""


# ------------------Enhanced Best Seller Offer Detail-----------------
class EnhancedBestSellerOfferDetailsSerializer(serializers.ModelSerializer):
    """
    EnhancedBestSellerOfferDetailsSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_offer_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    comments = serializers.CharField(read_only=True, default="")
    user = serializers.SerializerMethodField()
    master_offer = serializers.IntegerField(source="id", read_only=True, default="")
    buyer_id = serializers.IntegerField(source="user_id", read_only=True, default="")
    idx_property_id = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_detail",
                  "buyer_id", "can_offer_accept", "idx_property_id", "idx_property_image")

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = obj.offer_address_master_offer.filter(status=1).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            all_data['behalf_of_buyer'] = obj.behalf_of_buyer
            all_data['buyer_first_name'] = offer_address.buyer_first_name
            all_data['buyer_last_name'] = offer_address.buyer_last_name
            all_data['buyer_email'] = offer_address.buyer_email
            all_data['buyer_company'] = offer_address.buyer_company
            all_data['buyer_phone_no'] = offer_address.buyer_phone_no
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return EnhancedBestSellerOfferHistoryDetailSerializer(obj.highest_best_negotiated_offers_master_offer.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.accepted_by_id is not None and obj.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and not negotiated_offers.best_offer_is_accept and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_offer_accept(obj):
        try:
            negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None and obj.highest_best_negotiated_offers_master_offer.filter(status=1).count():
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                # offer_detail = OfferDetail.objects.filter(master_offer=obj.id).first()
                offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.id, offer_by=1, status=1).last()
                if offer_detail is not None:
                    data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                    data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                    data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                    data['closing_period'] = closing_period[offer_detail.closing_period]
                    data['financing'] = financing[offer_detail.financing]
                    data['offer_contingent'] = offer_detail.offer_contingent
                    data['sale_contingency'] = offer_detail.sale_contingency
                    data['down_payment'] = offer_detail.down_payment
                    data['appraisal_contingent'] = offer_detail.appraisal_contingent
                    data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_idx_property_id(obj):
        try:
            data = PropertyListing.objects.filter(id=obj.property_id).first()
            return data.idx_property_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                data = IdxPropertyUploads.filter(property=obj.property_id, status=1).first()
                all_data = {"id": data.id, "upload": data.upload}
                return all_data
            else:
                return {}
        except Exception as exp:
            return {}


class EnhancedBestSellerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    EnhancedBestSellerOfferHistoryDetailSerializer
    """

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "best_offer_is_accept", "offer_by", "is_declined", "property")

    @staticmethod
    def get_first_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.first_name
            else:
                return obj.master_offer.offer_address_master_offer.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.last_name
            else:
                return obj.master_offer.offer_address_master_offer.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer", 4: "Offer Declined"}
            return status[obj.display_status]
        except Exception as exp:
            return ""

# -------------------EnhancedBestOfferListingSerializer----------------------
class EnhancedBestOfferListingSerializer(serializers.ModelSerializer):
    """
    EnhancedBestOfferListingSerializer
    """
    property_image = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    auction_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    asking_price = serializers.SerializerMethodField()
    offer_status = serializers.SerializerMethodField()
    your_offer_price = serializers.SerializerMethodField()
    max_offer_price = serializers.SerializerMethodField()
    user_data = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "property_image", "domain_url", "auction_type",
                  "asking_price", "offer_status", "your_offer_price", "max_offer_price", "user_data",
                  "earnest_deposit_type", "offer_history", "can_accept", "can_counter", "can_reject", "status",
                  "auction_data")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_asking_price(obj):
        try:
            return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_offer_status(self, obj):
        try:
            data = obj.master_offer_property.filter(user=self.context).last()
            display_status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer", 4: "Offer Declined"}
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, master_offer__user=self.context, master_offer__is_declined=0, status=1, is_declined=0).last()
            if offer_data is not None and offer_data.best_offer_is_accept == 1:
                return "Offer Accepted"
            else:
                if data.accepted_by is not None:
                    return "Offer Accepted" if data.accepted_by_id == data.user_id else "Offer Accepted by seller"
                elif obj.status_id != 1:
                    return "Sold"
                elif data.is_declined:
                    return "Offer Rejected" if data.declined_by_id == data.user_id else "Offer Rejected by seller"
                else:
                    data = obj.highest_best_negotiated_offers_property.filter(master_offer__user=self.context, status=1).last()
                    return display_status[data.display_status]
        except Exception as exp:
            return ""

    def get_your_offer_price(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            return obj.highest_best_negotiated_offers_property.filter(master_offer=master_offer.id, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_max_offer_price(obj):
        try:
            return obj.highest_best_negotiated_offers_property.last().offer_price
        except Exception as exp:
            return ""

    def get_user_data(self, obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            offer_address = OfferAddress.objects.filter(master_offer__user=self.context, master_offer__property=obj.id).first()
            # offer_detail = OfferDetail.objects.filter(master_offer__user=self.context, master_offer__property=obj.id).first()
            offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer__user=self.context, master_offer__property=obj.id).last()
            data['first_name'] = offer_address.first_name if offer_address is not None else ""
            data['last_name'] = offer_address.last_name if offer_address is not None else ""
            data['email'] = offer_address.email if offer_address is not None else ""
            data['address_first'] = offer_address.address_first if offer_address is not None else ""
            data['city'] = offer_address.city if offer_address is not None else ""
            data['state'] = offer_address.state.state_name if offer_address is not None else ""
            data['phone_no'] = offer_address.phone_no if offer_address is not None else ""
            data['postal_code'] = offer_address.postal_code if offer_address is not None else ""
            data['buyer_first_name'] = offer_address.buyer_first_name if offer_address is not None else ""
            data['buyer_last_name'] = offer_address.buyer_last_name if offer_address is not None else ""
            data['buyer_email'] = offer_address.buyer_email if offer_address is not None else ""
            data['buyer_company'] = offer_address.buyer_company if offer_address is not None else ""
            data['buyer_phone_no'] = offer_address.buyer_phone_no if offer_address is not None else ""
            data['user_type'] = offer_address.master_offer.user_type if offer_address is not None else ""
            data['behalf_of_buyer'] = offer_address.master_offer.behalf_of_buyer if offer_address is not None else ""
            data['earnest_money_deposit'] = offer_detail.earnest_money_deposit if offer_detail is not None else ""
            data['due_diligence_period'] = offer_detail.due_diligence_period if offer_detail is not None else ""
            data['closing_period'] = offer_detail.closing_period if offer_detail is not None else ""
            data['negotiation_id'] = offer_detail.master_offer.id if offer_detail is not None else ""
            data['financing'] = financing[offer_detail.financing] if offer_detail is not None and offer_detail.financing is not None else ""
            data['down_payment'] = offer_detail.down_payment if offer_detail is not None else ""
            data['appraisal_contingent'] = offer_detail.appraisal_contingent if offer_detail is not None else ""
            data['closing_cost'] = offer_detail.closing_cost if offer_detail is not None else ""
            data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period] if offer_detail is not None and offer_detail.due_diligence_period is not None else ""
            data['closing_period'] = closing_period[offer_detail.closing_period] if offer_detail is not None and offer_detail.closing_period is not None else  ""
            data['offer_contingent'] = offer_contingent[offer_detail.offer_contingent] if offer_detail is not None and offer_detail.offer_contingent is not None else ""
            data['sale_contingency'] = offer_detail.sale_contingency if offer_detail is not None else ""
            return data
        except Exception as exp:
            return {}

    def get_offer_history(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            return EnhancedBuyerOfferHistoryDetailSerializer(HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    def get_can_accept(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if negotiated_offers.offer_by == 2 and not negotiated_offers.best_offer_is_accept and obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_can_counter(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_can_reject(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=obj.id, user=self.context).first()
            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
            if obj.status_id == 1 and not negotiated_offers.master_offer.is_canceled and not negotiated_offers.master_offer.is_declined and negotiated_offers.master_offer.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_auction_data(obj):
        try:
            data = {}
            auction = obj.property_auction.first()
            data['start_date'] = auction.start_date
            data['end_date'] = auction.end_date
            return data
        except Exception as exp:
            return {}


class EnhancedBuyerOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    EnhancedBuyerOfferHistoryDetailSerializer
    """

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_declined = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "first_name", "last_name", "user", "offer_price", "status", "added_on", "comments",
                  "offer_by", "is_declined")

    @staticmethod
    def get_first_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.first_name
            else:
                return obj.master_offer.offer_address_master_offer.first().first_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_name(obj):
        try:
            if obj.offer_by == 2:
                return obj.user.last_name
            else:
                return obj.master_offer.offer_address_master_offer.first().last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            status = {1: "Offer Pending", 2: "Counter Offer By Seller", 3: "Current Highest Offer", 4: "Offer Declined"}
            return status[obj.display_status]
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_declined(obj):
        try:
            if obj.master_offer.is_declined == 1 and obj.display_status == 4:
                return True
            else:
                return False
        except Exception as exp:
            return ""


class EnhancedBestFinalDetailSerializer(serializers.ModelSerializer):
    """
    EnhancedBestFinalDetailSerializer
    """
    user_detail = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    property = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    is_update = serializers.SerializerMethodField()
    current_offer_detail = serializers.SerializerMethodField()
    property_asset = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "user_detail", "offer_detail", "documents", "first_name", "last_name", "email", "phone_no", "address",
                  "property", "company_name", "auction_data", "is_update", "current_offer_detail", "property_asset")

    def get_user_detail(self, obj):
        try:
            data = {}
            offer_address = OfferAddress.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).first()
            if offer_address is not None:
                data['first_name'] = offer_address.first_name
                data['last_name'] = offer_address.last_name
                data['email'] = offer_address.email
                data['address_first'] = offer_address.address_first
                data['city'] = offer_address.city
                data['state_id'] = offer_address.state_id
                data['state'] = offer_address.state.state_name
                data['phone_no'] = offer_address.phone_no
                data['postal_code'] = offer_address.postal_code
                data['buyer_first_name'] = offer_address.buyer_first_name
                data['buyer_last_name'] = offer_address.buyer_last_name
                data['buyer_email'] = offer_address.buyer_email
                data['buyer_company'] = offer_address.buyer_company
                data['buyer_phone_no'] = offer_address.buyer_phone_no
                data['country'] = offer_address.country_id
            else:
                address = obj.profile_address_user.filter(address_type=1, status=1).first()
                data['first_name'] = obj.first_name
                data['last_name'] = obj.last_name
                data['email'] = obj.email
                data['address_first'] = address.address_first if address is not None else ""
                data['city'] = address.city if address is not None else ""
                data['state_id'] = address.state_id if address is not None else ""
                data['state'] = address.state.state_name if address is not None else ""
                data['phone_no'] = address.phone_no if address is not None else ""
                data['postal_code'] = address.postal_code if address is not None else ""
                data['buyer_first_name'] = ""
                data['buyer_last_name'] = ""
                data['buyer_email'] = ""
                data['buyer_company'] = ""
                data['buyer_phone_no'] = ""
                data['country'] = None
            return data
        except Exception as exp:
            return {}

    def get_offer_detail(self, obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            # offer_detail = OfferDetail.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).first()
            offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).last()
            if offer_detail is not None:
                data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                data['closing_period'] = closing_period[offer_detail.closing_period]
                data['financing'] = financing[offer_detail.financing]
                data['due_diligence_period_id'] = offer_detail.due_diligence_period
                data['closing_period_id'] = offer_detail.closing_period
                data['financing_id'] = offer_detail.financing
                data['offer_contingent'] = offer_detail.offer_contingent
                data['sale_contingency'] = offer_detail.sale_contingency
                # data['user_type'] = offer_detail.master_offer.user_type
                # data['working_with_agent'] = offer_detail.master_offer.working_with_agent
                # data['property_in_person'] = offer_detail.master_offer.property_in_person
                # data['pre_qualified_lender'] = offer_detail.master_offer.pre_qualified_lender
                # data['step'] = offer_detail.master_offer.steps
                data['down_payment'] = offer_detail.down_payment
                data['appraisal_contingent'] = offer_detail.appraisal_contingent
                data['closing_cost'] = offer_detail.closing_cost

            master_offer = MasterOffer.objects.filter(property=self.context, user=obj.id).first()
            if master_offer is not None:
                data['user_type'] = master_offer.user_type
                data['working_with_agent'] = master_offer.working_with_agent
                data['property_in_person'] = master_offer.property_in_person
                data['pre_qualified_lender'] = master_offer.pre_qualified_lender
                data['step'] = master_offer.steps
                data['document_comment'] = master_offer.document_comment
                data['behalf_of_buyer'] = master_offer.behalf_of_buyer
                offer_amount = master_offer.highest_best_negotiated_offers_master_offer.filter(user=obj.id, offer_by=1, status=1).last()
                data['current_offer_price'] = offer_amount.offer_price if offer_amount is not None else ""
            current_offer_detail = {}
            current_highest_amount = master_offer.highest_best_negotiated_offers_master_offer.filter(best_offer_is_accept=1, status=1).order_by("offer_price").last()
            if current_highest_amount is not None:
                current_offer_detail['current_offer_amount'] = current_highest_amount.offer_price if current_highest_amount is not None else ""
                # current_highest_detail = master_offer.offer_detail_master_offer.filter(master_offer=current_highest_amount.master_offer_id, status=1).last()
                # current_offer_detail['financing'] = financing[current_highest_detail.financing]
                # current_offer_detail['down_payment'] = current_highest_detail.down_payment
                # current_offer_detail['offer_contingent'] = offer_contingent[current_highest_detail.offer_contingent]
                # current_offer_detail['appraisal_contingent'] = current_highest_detail.appraisal_contingent
                # current_offer_detail['sale_contingency'] = current_highest_detail.sale_contingency
                # current_offer_detail['closing_period'] = closing_period[current_highest_detail.closing_period]
                # current_offer_detail['closing_cost'] = current_highest_detail.closing_cost
                current_offer_detail['financing'] = financing[current_highest_amount.financing]
                current_offer_detail['down_payment'] = current_highest_amount.down_payment
                current_offer_detail['offer_contingent'] = offer_contingent[current_highest_amount.offer_contingent]
                current_offer_detail['appraisal_contingent'] = current_highest_amount.appraisal_contingent
                current_offer_detail['sale_contingency'] = current_highest_amount.sale_contingency
                current_offer_detail['closing_period'] = closing_period[current_highest_amount.closing_period]
                current_offer_detail['closing_cost'] = current_highest_amount.closing_cost
            data['current_offer_detail'] = current_offer_detail
            return data
        except Exception as exp:
            return {}

    def get_documents(self, obj):
        try:
            offer_documents = OfferDocuments.objects.filter(master_offer__property=self.context, master_offer__user=obj.id).values("id", "document_id", doc_file_name=F("document__doc_file_name"), bucket_name=F("document__bucket_name"))
            return offer_documents
        except Exception as exp:
            return {}

    @staticmethod
    def get_address(obj):
        try:
            return BestFinalAddressSerializer(obj.profile_address_user.filter(address_type=1, status=1).first()).data
        except Exception as exp:
            return {}

    def get_property(self, obj):
        try:
            property_data = PropertyListing.objects.get(id=int(self.context))
            return BestFinalPropertySerializer(property_data).data
        except Exception as exp:
            return {}

    def get_company_name(self, obj):
        try:
            return PropertyListing.objects.get(id=int(self.context), status=1).domain.domain_name
        except Exception as exp:
            return ""

    def get_auction_data(self, obj):
        try:
            data = {}
            auction_data = PropertyAuction.objects.filter(property_id=int(self.context)).first()
            if auction_data is not None:
                data['id'] = auction_data.id
                data['start_date'] = auction_data.start_date
                data['end_date'] = auction_data.end_date
                data['start_price'] = auction_data.start_price
                data['un_priced'] = auction_data.un_priced
            return data
        except Exception as exp:
            return {}

    def get_is_update(self, obj):
        try:
            master_offer = MasterOffer.objects.filter(property=self.context, user=obj.id, is_canceled=0, is_declined=0).first()
            return True if master_offer is not None else False
        except Exception as exp:
            return ""

    def get_current_offer_detail(self, obj):
        try:
            current_offer_detail = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.",
                                    3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            current_highest_amount = HighestBestNegotiatedOffers.objects.filter(property=self.context, best_offer_is_accept=1, is_declined=0, master_offer__is_declined=0, status=1).last()

            if current_highest_amount is not None:
                current_offer_detail['current_offer_amount'] = current_highest_amount.offer_price if current_highest_amount is not None else ""
                # current_highest_detail = OfferDetail.objects.filter(master_offer=current_highest_amount.master_offer_id, status=1).last()
                # current_offer_detail['earnest_money_deposit'] = current_highest_detail.earnest_money_deposit
                # current_offer_detail['financing'] = financing[current_highest_detail.financing]
                # current_offer_detail['down_payment'] = current_highest_detail.down_payment
                # current_offer_detail['due_diligence_period'] = due_diligence_period[current_highest_detail.due_diligence_period]
                # current_offer_detail['offer_contingent'] = offer_contingent[current_highest_detail.offer_contingent]
                # current_offer_detail['appraisal_contingent'] = current_highest_detail.appraisal_contingent
                # current_offer_detail['sale_contingency'] = current_highest_detail.sale_contingency
                # current_offer_detail['closing_period'] = closing_period[current_highest_detail.closing_period]
                # current_offer_detail['closing_cost'] = current_highest_detail.closing_cost
                current_offer_detail['earnest_money_deposit'] = current_highest_amount.earnest_money_deposit
                current_offer_detail['financing'] = financing[current_highest_amount.financing]
                current_offer_detail['down_payment'] = current_highest_amount.down_payment
                current_offer_detail['due_diligence_period'] = due_diligence_period[current_highest_amount.due_diligence_period]
                current_offer_detail['offer_contingent'] = offer_contingent[current_highest_amount.offer_contingent]
                current_offer_detail['appraisal_contingent'] = current_highest_amount.appraisal_contingent
                current_offer_detail['sale_contingency'] = current_highest_amount.sale_contingency
                current_offer_detail['closing_period'] = closing_period[current_highest_amount.closing_period]
                current_offer_detail['closing_cost'] = current_highest_amount.closing_cost
            return current_offer_detail
        except Exception as exp:
            return {}

    def get_property_asset(self, obj):
        try:
            # master_offer = MasterOffer.objects.filter(property=int(self.context), user=obj.id).first()
            # return master_offer.property.property_asset_id
            property_listing = PropertyListing.objects.filter(id=int(self.context)).first()
            return property_listing.property_asset_id
        except Exception as exp:
            return ""


# -------------------------BestCounterBuyerOfferDetailSerializer------------------
class BestCounterBuyerOfferDetailSerializer(serializers.ModelSerializer):
    """
    BestCounterBuyerOfferDetailSerializer
    """

    earnest_deposit_type = serializers.IntegerField(source="property.earnest_deposit_type", read_only=True, default="")
    negotiation_id = serializers.IntegerField(source="master_offer.id", read_only=True, default="")
    financing = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()
    cancel_reason = serializers.CharField(source="master_offer.declined_reason", read_only=True, default="")
    property_asset = serializers.CharField(source="property.property_asset_id", read_only=True, default="")

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property", "earnest_deposit_type", "negotiation_id", "offer_by", "offer_price", "financing",
                  "down_payment", "earnest_money_deposit", "due_diligence_period", "offer_contingent",
                  "sale_contingency", "appraisal_contingent", "closing_period", "closing_cost", "buyer_detail",
                  "cancel_reason", "comments", "property_asset")

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            buyer_detail = {}
            agent_detail = {}
            address = obj.master_offer.offer_address_master_offer.first()
            if obj.master_offer.behalf_of_buyer == 1 and address is not None:
                agent_detail['first_name'] = address.first_name
                agent_detail['last_name'] = address.last_name
                agent_detail['email'] = address.email
                agent_detail['address_first'] = address.address_first
                agent_detail['city'] = address.city
                agent_detail['state'] = address.state.state_name
                agent_detail['phone_no'] = address.phone_no
                agent_detail['postal_code'] = address.postal_code

                buyer_detail['first_name'] = address.buyer_first_name
                buyer_detail['last_name'] = address.buyer_last_name
                buyer_detail['email'] = address.buyer_email
                buyer_detail['company'] = address.buyer_company
                buyer_detail['phone_no'] = address.buyer_phone_no
            elif address is not None:
                buyer_detail['first_name'] = address.first_name
                buyer_detail['last_name'] = address.last_name
                buyer_detail['email'] = address.email
                buyer_detail['address_first'] = address.address_first
                buyer_detail['city'] = address.city
                buyer_detail['state'] = address.state.state_name
                buyer_detail['phone_no'] = address.phone_no
                buyer_detail['postal_code'] = address.postal_code

            data['buyer_detail'] = buyer_detail
            data['agent_detail'] = agent_detail
            data['behalf_of_buyer'] = obj.master_offer.behalf_of_buyer
            return data
        except Exception as exp:
            return {}


# -------------------------ExtraBestCounterBuyerOfferDetailSerializer------------------
class ExtraBestCounterBuyerOfferDetailSerializer(serializers.ModelSerializer):
    """
    ExtraBestCounterBuyerOfferDetailSerializer
    """

    earnest_deposit_type = serializers.IntegerField(source="property.earnest_deposit_type", read_only=True, default="")
    negotiation_id = serializers.IntegerField(source="master_offer.id", read_only=True, default="")
    buyer_detail = serializers.SerializerMethodField()
    cancel_reason = serializers.CharField(source="master_offer.declined_reason", read_only=True, default="")
    property_asset = serializers.CharField(source="property.property_asset_id", read_only=True, default="")

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property", "earnest_deposit_type", "negotiation_id", "buyer_detail", "cancel_reason",
                  "comments", "property_asset")

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}

            buyer_detail = {}
            agent_detail = {}
            address = obj.master_offer.offer_address_master_offer.first()
            if obj.master_offer.behalf_of_buyer == 1 and address is not None:
                agent_detail['first_name'] = address.first_name
                agent_detail['last_name'] = address.last_name
                agent_detail['email'] = address.email
                agent_detail['address_first'] = address.address_first
                agent_detail['city'] = address.city
                agent_detail['state'] = address.state.state_name
                agent_detail['phone_no'] = address.phone_no
                agent_detail['postal_code'] = address.postal_code

                buyer_detail['first_name'] = address.buyer_first_name
                buyer_detail['last_name'] = address.buyer_last_name
                buyer_detail['email'] = address.buyer_email
                buyer_detail['company'] = address.buyer_company
                buyer_detail['phone_no'] = address.buyer_phone_no
            elif address is not None:
                buyer_detail['first_name'] = address.first_name
                buyer_detail['last_name'] = address.last_name
                buyer_detail['email'] = address.email
                buyer_detail['address_first'] = address.address_first
                buyer_detail['city'] = address.city
                buyer_detail['state'] = address.state.state_name
                buyer_detail['phone_no'] = address.phone_no
                buyer_detail['postal_code'] = address.postal_code

            data['buyer_detail'] = buyer_detail
            data['agent_detail'] = agent_detail
            data['behalf_of_buyer'] = obj.master_offer.behalf_of_buyer
            return data
        except Exception as exp:
            return {}


# -------------------------BestCounterSellerOfferDetailSerializer------------------
class BestCounterSellerOfferDetailSerializer(serializers.ModelSerializer):
    """
    BestCounterSellerOfferDetailSerializer
    """

    earnest_deposit_type = serializers.IntegerField(source="property.earnest_deposit_type", read_only=True, default="")
    negotiation_id = serializers.IntegerField(source="master_offer.id", read_only=True, default="")
    financing = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()
    cancel_reason = serializers.CharField(source="master_offer.cancel_reason", read_only=True, default="")
    property_asset = serializers.CharField(source="property.property_asset_id", read_only=True, default="")

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property", "earnest_deposit_type", "negotiation_id", "offer_by", "offer_price", "financing",
                  "down_payment", "earnest_money_deposit", "due_diligence_period", "offer_contingent",
                  "sale_contingency", "appraisal_contingent", "closing_period", "closing_cost", "buyer_detail",
                  "cancel_reason", "property_asset")

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            buyer_detail = {}
            agent_detail = {}
            address = obj.master_offer.offer_address_master_offer.first()
            if obj.master_offer.behalf_of_buyer == 1 and address is not None:
                agent_detail['first_name'] = address.first_name
                agent_detail['last_name'] = address.last_name
                agent_detail['email'] = address.email
                agent_detail['address_first'] = address.address_first
                agent_detail['city'] = address.city
                agent_detail['state'] = address.state.state_name
                agent_detail['phone_no'] = address.phone_no
                agent_detail['postal_code'] = address.postal_code

                buyer_detail['first_name'] = address.buyer_first_name
                buyer_detail['last_name'] = address.buyer_last_name
                buyer_detail['email'] = address.buyer_email
                buyer_detail['company'] = address.buyer_company
                buyer_detail['phone_no'] = address.buyer_phone_no
            elif address is not None:
                buyer_detail['first_name'] = address.first_name
                buyer_detail['last_name'] = address.last_name
                buyer_detail['email'] = address.email
                buyer_detail['address_first'] = address.address_first
                buyer_detail['city'] = address.city
                buyer_detail['state'] = address.state.state_name
                buyer_detail['phone_no'] = address.phone_no
                buyer_detail['postal_code'] = address.postal_code

            data['buyer_detail'] = buyer_detail
            data['agent_detail'] = agent_detail
            data['behalf_of_buyer'] = obj.master_offer.behalf_of_buyer
            return data
        except Exception as exp:
            return {}


class EnhancedBestCurrentOfferSerializer(serializers.ModelSerializer):
    """
    EnhancedBestCurrentOfferSerializer
    """

    earnest_money_deposit = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    closing_date = serializers.SerializerMethodField()
    earnest_deposit_type = serializers.SerializerMethodField()
    financing = serializers.SerializerMethodField()
    down_payment = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    appraisal_contingent = serializers.SerializerMethodField()
    sale_contingency = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    closing_cost = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "offer_price", "earnest_money_deposit", "due_diligence_period", "closing_date",
                  "earnest_deposit_type", "financing", "down_payment", "earnest_money_deposit",
                  "due_diligence_period", "offer_contingent", "appraisal_contingent", "sale_contingency",
                  "closing_period", "closing_cost")

    @staticmethod
    def get_earnest_money_deposit(obj):
        try:
            return obj.earnest_money_deposit
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_date(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_earnest_deposit_type(obj):
        try:
            return obj.property.earnest_deposit_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_down_payment(obj):
        try:
            return obj.down_payment
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_appraisal_contingent(obj):
        try:
            return obj.appraisal_contingent
        except Exception as exp:
            return ""

    @staticmethod
    def get_sale_contingency(obj):
        try:
            return obj.sale_contingency
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_cost(obj):
        try:
            return obj.closing_cost
        except Exception as exp:
            return ""


# -------------------------BestOfferHistoryDetailSerializer------------------
class BestOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    BestOfferHistoryDetailSerializer
    """

    earnest_deposit_type = serializers.IntegerField(source="property.earnest_deposit_type", read_only=True, default="")
    negotiation_id = serializers.IntegerField(source="master_offer.id", read_only=True, default="")
    financing = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property", "earnest_deposit_type", "negotiation_id", "offer_by", "offer_price", "financing",
                  "down_payment", "earnest_money_deposit", "due_diligence_period", "offer_contingent",
                  "sale_contingency", "appraisal_contingent", "closing_period", "closing_cost", "buyer_detail",
                  "declined_reason", "comments", "offer_by")

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            buyer_detail = {}
            agent_detail = {}
            address = obj.master_offer.offer_address_master_offer.first()
            if obj.master_offer.behalf_of_buyer == 1 and address is not None:
                agent_detail['first_name'] = address.first_name
                agent_detail['last_name'] = address.last_name
                agent_detail['email'] = address.email
                agent_detail['address_first'] = address.address_first
                agent_detail['city'] = address.city
                agent_detail['state'] = address.state.state_name
                agent_detail['phone_no'] = address.phone_no
                agent_detail['postal_code'] = address.postal_code

                buyer_detail['first_name'] = address.buyer_first_name
                buyer_detail['last_name'] = address.buyer_last_name
                buyer_detail['email'] = address.buyer_email
                buyer_detail['company'] = address.buyer_company
                buyer_detail['phone_no'] = address.buyer_phone_no
            elif address is not None:
                buyer_detail['first_name'] = address.first_name
                buyer_detail['last_name'] = address.last_name
                buyer_detail['email'] = address.email
                buyer_detail['address_first'] = address.address_first
                buyer_detail['city'] = address.city
                buyer_detail['state'] = address.state.state_name
                buyer_detail['phone_no'] = address.phone_no
                buyer_detail['postal_code'] = address.postal_code

            data['buyer_detail'] = buyer_detail
            data['agent_detail'] = agent_detail
            data['behalf_of_buyer'] = obj.master_offer.behalf_of_buyer
            return data
        except Exception as exp:
            return {}


# ----------------SuperAdminSellerOfferListingSerializer------------------
class SuperAdminSellerOfferListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminSellerOfferListingSerializer
    """
    buyer = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    offer_price_detail = serializers.SerializerMethodField()
    highest_offer_user = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        fields = ("id", "buyer", "offer_price", "date", "property", "document", "offer_price_detail", "is_declined", "highest_offer_user")

    @staticmethod
    def get_buyer(obj):
        try:
            if obj.property.sale_by_type_id == 4:
                data = obj.negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data = {}
                all_data['first_name'] = data.user.first_name
                all_data['last_name'] = data.user.last_name
                all_data['email'] = data.user.email
                all_data['id'] = data.user_id
            else:
                data = obj.offer_address_master_offer.filter(status=1).last()
                all_data = {}
                all_data['first_name'] = data.first_name
                all_data['last_name'] = data.last_name
                all_data['email'] = data.email
                all_data['id'] = obj.user_id
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_price(obj):
        try:
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            return data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_date(obj):
        try:
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                data = last_data
            else:
                data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
            if data is not None:
                return data.added_on
            else:
                return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.document.doc_file_name
            # data['bucket_name'] = obj.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_offer_price_detail(obj):
        try:
            all_data = {}
            last_data = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            all_data['best_offer_is_accept'] = last_data.best_offer_is_accept
            if last_data.offer_by == 2 and last_data.best_offer_is_accept == 1:
                all_data['price'] = last_data.offer_price
            else:
                last_data = obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last()
                all_data['price'] = last_data.offer_price
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_highest_offer_user(obj):
        try:
            highest_offer = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.property_id, best_offer_is_accept=1, is_declined=0, master_offer__is_declined=0).order_by("offer_price").last()
            return highest_offer.master_offer.user_id
        except Exception as exp:
            return ""


# ------------------SuperAdminBestSellerOfferDetailsSerializer-----------------
class SuperAdminBestSellerOfferDetailsSerializer(serializers.ModelSerializer):
    """
    SuperAdminBestSellerOfferDetailsSerializer
    """
    property_detail = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    offer_history = serializers.SerializerMethodField()
    auction_type_name = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    can_action = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    asking_price = serializers.SerializerMethodField()
    is_sold = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()
    can_offer_accept = serializers.SerializerMethodField()
    can_counter = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()
    comments = serializers.CharField(read_only=True, default="")
    user = serializers.SerializerMethodField()
    master_offer = serializers.IntegerField(source="id", read_only=True, default="")
    buyer_id = serializers.IntegerField(source="user_id", read_only=True, default="")

    class Meta:
        model = MasterOffer
        fields = ("id", "property_detail", "user_detail", "offer_price", "added_on", "comments", "offer_history", "user",
                  "auction_type_name", "can_action", "master_offer", "property", "is_rejected", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "document", "asking_price",
                  "is_sold", "is_accepted", "is_rejected", "can_accept", "can_counter", "can_reject", "offer_detail",
                  "buyer_id", "can_offer_accept")

    @staticmethod
    def get_offer_price(obj):
        try:
            return obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last().offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_user(obj):
        try:
            return obj.highest_best_negotiated_offers_master_offer.filter(offer_by=1, status=1).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_detail(obj):
        try:
            return OfferPropertyDetailSerializer(PropertyListing.objects.filter(id=obj.property_id, sale_by_type__in=[4, 7]).first()).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            all_data = {}
            offer_address = obj.offer_address_master_offer.filter(status=1).first()
            # all_data['first_name'] = obj.user.first_name
            # all_data['last_name'] = obj.user.last_name
            # all_data['email'] = obj.user.email
            # all_data['phone_no'] = obj.user.phone_no
            all_data['first_name'] = offer_address.first_name
            all_data['last_name'] = offer_address.last_name
            all_data['email'] = offer_address.email
            all_data['phone_no'] = offer_address.phone_no
            all_data['address_first'] = offer_address.address_first
            all_data['city'] = offer_address.city
            all_data['state'] = offer_address.state.state_name
            all_data['postal_code'] = offer_address.postal_code
            all_data['behalf_of_buyer'] = obj.behalf_of_buyer
            all_data['buyer_first_name'] = offer_address.buyer_first_name
            all_data['buyer_last_name'] = offer_address.buyer_last_name
            all_data['buyer_email'] = offer_address.buyer_email
            all_data['buyer_company'] = offer_address.buyer_company
            all_data['buyer_phone_no'] = offer_address.buyer_phone_no
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_offer_history(obj):
        try:
            return EnhancedBestSellerOfferHistoryDetailSerializer(obj.highest_best_negotiated_offers_master_offer.filter(status=1).order_by("-id"), many=True).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_action(obj):
        try:
            if obj.property.status_id == 1:
                last_negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
                if last_negotiated_offers.offer_by == 1 and not obj.master_offer.is_canceled and not obj.master_offer.is_declined:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_rejected(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.property.status_id == 1:
                if obj.is_canceled == 1 or obj.is_declined == 1:
                    return True
                else:
                    return False
            else:
                return True
        except Exception as exp:
            return False

    @staticmethod
    def get_document(obj):
        try:
            # data = {}
            # data['doc_file_name'] = obj.master_offer.document.doc_file_name
            # data['bucket_name'] = obj.master_offer.document.bucket_name
            # return data
            return obj.offer_documents_master_offer.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_asking_price(obj):
        try:
            return PropertyAuction.objects.filter(property=obj.property_id).first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_sold(obj):
        try:
            return True if obj.property.status_id == 9 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_is_accepted(obj):
        try:
            data = {}
            if obj.accepted_by_id is not None and obj.accepted_by_id > 0:
                data['accepted'] = True
                data['accepted_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_is_rejected(obj):
        try:
            data = {}
            if obj.is_declined == 1:
                data['declined'] = True
                data['declined_by'] = "Buyer" if obj.final_by == 1 else "Seller"
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_can_accept(obj):
        try:
            negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and not negotiated_offers.best_offer_is_accept and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_offer_accept(obj):
        try:
            negotiated_offers = obj.highest_best_negotiated_offers_master_offer.filter(status=1).last()
            if negotiated_offers.offer_by == 1 and obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_counter(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None and obj.highest_best_negotiated_offers_master_offer.filter(status=1).count():
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_can_reject(obj):
        try:
            if obj.property.status_id == 1 and not obj.is_canceled and not obj.is_declined and obj.accepted_by is None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            if obj.property.sale_by_type_id == 7:
                # offer_detail = OfferDetail.objects.filter(master_offer=obj.id).first()
                offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.id, offer_by=1, status=1).last()
                if offer_detail is not None:
                    data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
                    data['earnest_deposit_type'] = obj.property.earnest_deposit_type
                    data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
                    data['closing_period'] = closing_period[offer_detail.closing_period]
                    data['financing'] = financing[offer_detail.financing]
                    data['offer_contingent'] = offer_detail.offer_contingent
                    data['sale_contingency'] = offer_detail.sale_contingency
                    data['down_payment'] = offer_detail.down_payment
                    data['appraisal_contingent'] = offer_detail.appraisal_contingent
                    data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}


# -------------------------SuperAdminBestOfferHistoryDetailSerializer------------------
class SuperAdminBestOfferHistoryDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminBestOfferHistoryDetailSerializer
    """

    earnest_deposit_type = serializers.IntegerField(source="property.earnest_deposit_type", read_only=True, default="")
    negotiation_id = serializers.IntegerField(source="master_offer.id", read_only=True, default="")
    financing = serializers.SerializerMethodField()
    due_diligence_period = serializers.SerializerMethodField()
    offer_contingent = serializers.SerializerMethodField()
    closing_period = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()

    class Meta:
        model = HighestBestNegotiatedOffers
        fields = ("id", "property", "earnest_deposit_type", "negotiation_id", "offer_by", "offer_price", "financing",
                  "down_payment", "earnest_money_deposit", "due_diligence_period", "offer_contingent",
                  "sale_contingency", "appraisal_contingent", "closing_period", "closing_cost", "buyer_detail",
                  "declined_reason", "comments", "offer_by")

    @staticmethod
    def get_financing(obj):
        try:
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
            return financing[obj.financing]
        except Exception as exp:
            return ""

    @staticmethod
    def get_due_diligence_period(obj):
        try:
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
            return due_diligence_period[obj.due_diligence_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_offer_contingent(obj):
        try:
            offer_contingent = {1: "Yes", 2: "No", 3: "Cash Buyer"}
            return offer_contingent[obj.offer_contingent]
        except Exception as exp:
            return ""

    @staticmethod
    def get_closing_period(obj):
        try:
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            return closing_period[obj.closing_period]
        except Exception as exp:
            return ""

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            buyer_detail = {}
            agent_detail = {}
            address = obj.master_offer.offer_address_master_offer.first()
            if obj.master_offer.behalf_of_buyer == 1 and address is not None:
                agent_detail['first_name'] = address.first_name
                agent_detail['last_name'] = address.last_name
                agent_detail['email'] = address.email
                agent_detail['address_first'] = address.address_first
                agent_detail['city'] = address.city
                agent_detail['state'] = address.state.state_name
                agent_detail['phone_no'] = address.phone_no
                agent_detail['postal_code'] = address.postal_code

                buyer_detail['first_name'] = address.buyer_first_name
                buyer_detail['last_name'] = address.buyer_last_name
                buyer_detail['email'] = address.buyer_email
                buyer_detail['company'] = address.buyer_company
                buyer_detail['phone_no'] = address.buyer_phone_no
            elif address is not None:
                buyer_detail['first_name'] = address.first_name
                buyer_detail['last_name'] = address.last_name
                buyer_detail['email'] = address.email
                buyer_detail['address_first'] = address.address_first
                buyer_detail['city'] = address.city
                buyer_detail['state'] = address.state.state_name
                buyer_detail['phone_no'] = address.phone_no
                buyer_detail['postal_code'] = address.postal_code

            data['buyer_detail'] = buyer_detail
            data['agent_detail'] = agent_detail
            data['behalf_of_buyer'] = obj.master_offer.behalf_of_buyer
            return data
        except Exception as exp:
            return {}


class SuperAdminGetLoiSerializer(serializers.ModelSerializer):
    """
    SuperAdminGetLoiSerializer
    """
    user_detail = serializers.SerializerMethodField()
    property_detail = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    offer_detail = serializers.SerializerMethodField()
    buyer_detail = serializers.SerializerMethodField()

    class Meta:
        model = MasterOffer
        # fields = ("id", "user_detail", "property_detail", "auction_data", "offer_detail", "user_type",
        #           "working_with_agent", "property_in_person", "pre_qualified_lender")
        fields = ("id", "user_detail", "property_detail", "auction_data", "offer_detail", "user_type",
                  "working_with_agent", "property_in_person", "pre_qualified_lender", "behalf_of_buyer",
                  "buyer_detail")

    @staticmethod
    def get_user_detail(obj):
        try:
            data = {}
            offer_address = OfferAddress.objects.filter(master_offer=obj.id).first()
            data['first_name'] = offer_address.first_name
            data['last_name'] = offer_address.last_name
            data['email'] = offer_address.email
            data['address_first'] = offer_address.address_first
            data['city'] = offer_address.city
            data['state_id'] = offer_address.state_id
            data['state'] = offer_address.state.state_name
            data['phone_no'] = offer_address.phone_no
            data['postal_code'] = offer_address.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_detail(obj):
        try:
            return LoiPropertySerializer(obj.property).data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_data(obj):
        try:
            data = {}
            auction_data = PropertyAuction.objects.filter(property=obj.property_id).first()
            data['id'] = auction_data.id
            data['start_date'] = auction_data.start_date
            data['end_date'] = auction_data.end_date
            data['start_price'] = auction_data.start_price
            return data
        except Exception as exp:
            return {}

    # @staticmethod
    # def get_offer_detail(obj):
    #     try:
    #         data = {}
    #         due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.", 3: "16+ Days", 4: "Waive Inspection"}
    #         closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
    #         financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan", 6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan", 11: "Conduit/CMBS Loan"}
    #         # offer_detail = OfferDetail.objects.filter(master_offer=obj.id).first()
    #         offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.id, is_declined=0, status=1).last()
    #         data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
    #         data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
    #         data['closing_period'] = closing_period[offer_detail.closing_period]
    #         data['financing'] = financing[offer_detail.financing]
    #         data['due_diligence_period_id'] = offer_detail.due_diligence_period
    #         data['closing_period_id'] = offer_detail.closing_period
    #         data['financing_id'] = offer_detail.financing
    #         data['offer_contingent'] = offer_detail.offer_contingent
    #         data['sale_contingency'] = offer_detail.sale_contingency
    #         data['last_offer_price'] = offer_detail.offer_price
    #         return data
    #     except Exception as exp:
    #         return {}

    @staticmethod
    def get_offer_detail(obj):
        try:
            data = {}
            due_diligence_period = {1: "Yes, complete inspections at buyer(s) expense.", 2: "No, waive inspections.",
                                    3: "16+ Days", 4: "Waive Inspection"}
            closing_period = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}
            financing = {1: "No Loan", 2: "Conventional Loan", 3: "VA Loan", 4: "FHA Loan", 5: "SBA  Loan",
                         6: "1031 Exchange", 7: "Other", 8: "USDA/FSA Loan", 9: "Bridge Loan", 10: "Jumbo Loan",
                         11: "Conduit/CMBS Loan"}
            offer_detail = HighestBestNegotiatedOffers.objects.filter(master_offer=obj.id, is_declined=0, status=1).last()
            data['earnest_money_deposit'] = offer_detail.earnest_money_deposit
            data['due_diligence_period'] = due_diligence_period[offer_detail.due_diligence_period]
            data['closing_period'] = closing_period[offer_detail.closing_period]
            data['financing'] = financing[offer_detail.financing]
            data['due_diligence_period_id'] = offer_detail.due_diligence_period
            data['closing_period_id'] = offer_detail.closing_period
            data['financing_id'] = offer_detail.financing
            data['offer_contingent'] = offer_detail.offer_contingent
            data['sale_contingency'] = offer_detail.sale_contingency
            data['last_offer_price'] = offer_detail.offer_price
            data['down_payment'] = offer_detail.down_payment
            data['appraisal_contingency'] = offer_detail.appraisal_contingent
            data['closing_cost'] = offer_detail.closing_cost
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_buyer_detail(obj):
        try:
            data = {}
            if obj.behalf_of_buyer == 1:
                offer_address = OfferAddress.objects.filter(master_offer=obj.id).first()
                data['first_name'] = offer_address.buyer_first_name
                data['last_name'] = offer_address.buyer_last_name
                data['email'] = offer_address.buyer_email
                data['phone_no'] = offer_address.buyer_phone_no
            return data
        except Exception as exp:
            return {}


class DutchInsiderBidderSerializer(serializers.ModelSerializer):
    """
    DutchInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.start_date", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.dutch_end_time", read_only=True, default="")
    start_price = serializers.DecimalField(source="auction.start_price", max_digits=15, decimal_places=2, read_only=True, default="")
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.BooleanField(default=True, read_only=True)
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""
    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id,user_id=obj.user_id,domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class SealedInsiderBidderSerializer(serializers.ModelSerializer):
    """
    SealedInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.sealed_start_time", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.sealed_end_time", read_only=True, default="")
    start_price = serializers.SerializerMethodField()
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    @staticmethod
    def get_start_price(obj):
        try:
            return InsiderAuctionStepWinner.objects.filter(property=obj.property_id, insider_auction_step=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_winner(obj):
        try:
            winner_user = obj.insider_auction_step_winner_bid.filter(insider_auction_step=2).first().user_id
            return True if int(winner_user) == obj.user_id else False
        except Exception as exp:
            return False

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id, user_id=obj.user_id,
                                                      domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class EnglishInsiderBidderSerializer(serializers.ModelSerializer):
    """
    EnglishInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.start_date", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.dutch_end_time", read_only=True, default="")
    start_price = serializers.SerializerMethodField()
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    @staticmethod
    def get_start_price(obj):
        try:
            return InsiderAuctionStepWinner.objects.filter(property=obj.property_id, insider_auction_step=2).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_winner(obj):
        try:
            winner_user = obj.insider_auction_step_winner_bid.filter(insider_auction_step=3).first().user_id
            return True if int(winner_user) == obj.user_id else False
        except Exception as exp:
            return False

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id, user_id=obj.user_id,
                                                      domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class InlineBiddingListingSerializer(serializers.ModelSerializer):
    """
    InlineBiddingListingSerializer
    """
    property_image = serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    auction_type = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    broker_name = serializers.SerializerMethodField()
    my_bid = serializers.SerializerMethodField()
    current_bid = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    bid_increment = serializers.SerializerMethodField()
    registration_status = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    bid_start_date = serializers.SerializerMethodField()
    bid_end_date = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    auction_id = serializers.SerializerMethodField()
    start_price = serializers.SerializerMethodField()
    next_bid = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    auction_status = serializers.SerializerMethodField()
    decreased_amount = serializers.SerializerMethodField()
    round_one_winning_amount = serializers.SerializerMethodField()
    round_two_winning_amount = serializers.SerializerMethodField()
    round_three_winning_amount = serializers.SerializerMethodField()
    dutch_end_time = serializers.SerializerMethodField()
    sealed_start_time = serializers.SerializerMethodField()
    sealed_end_time = serializers.SerializerMethodField()
    english_start_time = serializers.SerializerMethodField()
    dutch_winning_user_id = serializers.SerializerMethodField()
    sealed_winning_user_id = serializers.SerializerMethodField()
    english_winning_user_id = serializers.SerializerMethodField()
    user_sealed_bid_amount = serializers.SerializerMethodField()

    class Meta:
        model = BidRegistration
        fields = ("id", "property_image", "property_address_one", "property_city", "property_state",
                  "property_postal_code", "auction_type", "company", "broker_name", "my_bid", "current_bid",
                  "bid_count", "bid_increment", "registration_status", "is_approved", "bid_start_date",
                  "bid_end_date", "property", "domain_url", "auction_id", "start_price", "next_bid", "approval_status",
                  "auction_status", "decreased_amount", "round_one_winning_amount", "round_two_winning_amount",
                  "round_three_winning_amount", "dutch_end_time", "sealed_start_time", "sealed_end_time",
                  "english_start_time", "dutch_winning_user_id", "sealed_winning_user_id", "english_winning_user_id",
                  "user_sealed_bid_amount")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_broker_name(obj):
        try:
            data = obj.domain.users_site_id.filter(status=1).first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_my_bid(obj):
        try:
            return obj.property.bid_property.filter(user=obj.user_id, bid_type__in=[2, 3], is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_bid(obj):
        try:
            return obj.property.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_count(obj):
        try:
            return obj.property.bid_property.filter(property=obj.property_id, bid_type__in=[2, 3]).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_increment(obj):
        try:
            return obj.property.property_auction.first().bid_increments
        except Exception as exp:
            return ""

    @staticmethod
    def get_registration_status(obj):
        try:
            approval = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
            if obj.is_approved == 2 and obj.is_reviewed:
                return "Approved"
            elif obj.is_approved == 2 and not obj.is_reviewed:
                return "Not Reviewed"
            else:
                return approval[int(obj.is_approved)]
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_approved(obj):
        try:
            if obj.is_approved == 2 and obj.is_reviewed == 1:
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bid_start_date(obj):
        try:
            return obj.property.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_end_date(obj):
        try:
            return obj.property.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_id(obj):
        try:
            return obj.property.property_auction.first().id
        except Exception as exp:
            return ""

    @staticmethod
    def get_start_price(obj):
        try:
            return obj.property.property_auction.first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_next_bid(obj):
        try:
            auction_data = obj.property.property_auction.last()
            bid_amount = obj.property.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if bid_amount is not None:
                return int(bid_amount.bid_amount) + int(auction_data.bid_increments)
            else:
                return int(auction_data.start_price)
        except Exception as exp:
            return ""

    @staticmethod
    def get_approval_status(obj):
        try:
            if obj.is_approved == 2 and obj.is_reviewed == 1:
                return "Registration Approved But Auction Not Started Yet"
            elif obj.is_approved == 3 or obj.is_approved == 4:
                return "Registration Declined"
            else:
                return "Registration Pending Approval"
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_status(obj):
        try:
            return obj.property.property_auction.first().status_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_decreased_amount(obj):
        try:
            return obj.property.property_auction.first().insider_decreased_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_one_winning_amount(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_two_winning_amount(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_three_winning_amount(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_end_time(obj):
        try:
            return obj.property.property_auction.first().dutch_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_start_time(obj):
        try:
            return obj.property.property_auction.first().sealed_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_end_time(obj):
        try:
            return obj.property.property_auction.first().sealed_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_start_time(obj):
        try:
            return obj.property.property_auction.first().english_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_winning_user_id(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_winning_user_id(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_winning_user_id(obj):
        try:
            return obj.property.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_sealed_bid_amount(obj):
        try:
            return obj.property.bid_property.filter(user=obj.user_id, insider_auction_step=2, is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""


class SuperAdminDutchInsiderBidderSerializer(serializers.ModelSerializer):
    """
    SuperAdminDutchInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.start_date", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.dutch_end_time", read_only=True, default="")
    start_price = serializers.DecimalField(source="auction.start_price", max_digits=15, decimal_places=2, read_only=True, default="")
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.BooleanField(default=True, read_only=True)
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""
    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id,user_id=obj.user_id,domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class SuperAdminSealedInsiderBidderSerializer(serializers.ModelSerializer):
    """
    SuperAdminSealedInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.sealed_start_time", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.sealed_end_time", read_only=True, default="")
    start_price = serializers.SerializerMethodField()
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    @staticmethod
    def get_start_price(obj):
        try:
            return InsiderAuctionStepWinner.objects.filter(property=obj.property_id, insider_auction_step=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_winner(obj):
        try:
            winner_user = obj.insider_auction_step_winner_bid.filter(insider_auction_step=2).first().user_id
            return True if int(winner_user) == obj.user_id else False
        except Exception as exp:
            return False

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id, user_id=obj.user_id,
                                                      domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class SuperAdminEnglishInsiderBidderSerializer(serializers.ModelSerializer):
    """
    SuperAdminEnglishInsiderBidderSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    company = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    bidding_start_time = serializers.DateTimeField(source="auction.start_date", read_only=True, default="")
    bidding_end_time = serializers.DateTimeField(source="auction.dutch_end_time", read_only=True, default="")
    start_price = serializers.SerializerMethodField()
    insider_decreased_price = serializers.FloatField(source="auction.insider_decreased_price", read_only=True, default="")
    is_winner = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = ("id", "first_name", "last_name", "phone_no", "ip_address", "bidding_start_time", "bidding_end_time",
                  "start_price", "insider_decreased_price", "bid_amount", "is_winner", "email", "company", "user_type")

    @staticmethod
    def get_start_price(obj):
        try:
            return InsiderAuctionStepWinner.objects.filter(property=obj.property_id, insider_auction_step=2).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_winner(obj):
        try:
            winner_user = obj.insider_auction_step_winner_bid.filter(insider_auction_step=3).first().user_id
            return True if int(winner_user) == obj.user_id else False
        except Exception as exp:
            return False

    # @staticmethod
    # def get_user_type(obj):
    #     try:
    #         data = Users.objects.filter(id=obj.user_id).first()
    #         if data.user_type_id == 2:
    #             if data.site_id is None and data.site_id == "":
    #                 return "Agent"
    #             else:
    #                 return "Broker"
    #         else:
    #             return data.user_type.user_type
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_user_type(obj):
        try:
            user_obj = BidRegistration.objects.filter(property_id=obj.property_id, user_id=obj.user_id,
                                                      domain_id=obj.domain_id).first()
            user_type_id = user_obj.user_type
            user_type = {1: "Investor", 2: "Buyer", 3: "Seller", 4: "Agent"}
            return user_type[int(user_type_id)]
        except Exception as exp:
            return ""


class SuperAdminInlineBiddingMonitorSerializer(serializers.ModelSerializer):
    """
    SuperAdminInlineBiddingMonitorSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    property_owner = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    current_bid = serializers.SerializerMethodField()
    high_bidder = serializers.SerializerMethodField()
    next_bid = serializers.SerializerMethodField()
    total_bids = serializers.SerializerMethodField()
    bidder = serializers.SerializerMethodField()
    watcher = serializers.SerializerMethodField()
    reserve_price = serializers.SerializerMethodField()
    reserve_met = serializers.SerializerMethodField()
    # high_bidder = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    decreased_amount = serializers.SerializerMethodField()
    round_one_winning_amount = serializers.SerializerMethodField()
    round_two_winning_amount = serializers.SerializerMethodField()
    round_three_winning_amount = serializers.SerializerMethodField()
    dutch_end_time = serializers.SerializerMethodField()
    sealed_start_time = serializers.SerializerMethodField()
    sealed_end_time = serializers.SerializerMethodField()
    english_start_time = serializers.SerializerMethodField()
    dutch_winning_user_id = serializers.SerializerMethodField()
    sealed_winning_user_id = serializers.SerializerMethodField()
    english_winning_user_id = serializers.SerializerMethodField()
    user_sealed_bid_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "status", "auction_data",
                  "current_bid", "high_bidder", "next_bid", "total_bids", "bidder", "watcher", "reserve_price",
                  "reserve_met", "property_owner", "read_by_auction_dashboard", "status_id", "domain", "domain_url",
                  "decreased_amount", "round_one_winning_amount", "round_two_winning_amount",
                  "round_three_winning_amount", "dutch_end_time", "sealed_start_time", "sealed_end_time", "english_start_time",
                  "dutch_winning_user_id", "sealed_winning_user_id", "english_winning_user_id", "user_sealed_bid_amount")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_owner(obj):
        try:
            all_data = {}
            all_data['first_name'] = obj.agent.first_name
            all_data['last_name'] = obj.agent.last_name
            all_data['company'] = obj.domain.domain_name
            all_data['phone_no'] = obj.agent.phone_no
            all_data['email'] = obj.agent.email
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_data(obj):
        try:
            auction = obj.property_auction.first()
            all_data = {
                "id": auction.id,
                "start_date": auction.start_date,
                "end_date": auction.end_date,
                "bid_increments": auction.bid_increments,
                "status": auction.status_id
            }
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_current_bid(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_high_bidder(obj):
        try:
            all_data = {}
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                if bidder.insider_auction_step == 2:
                    winner_step = obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first()
                    bidder = obj.bid_property.filter(id=winner_step.bid_id, is_canceled=0).last()
                high_bidder_id = bidder.user_id
                bidder_detail = BidRegistrationAddress.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, address_type__in=[2, 3], status=1).last()
                all_data['first_name'] = bidder_detail.first_name
                all_data['last_name'] = bidder_detail.last_name
                all_data['registration_id'] = bidder_detail.registration.registration_id
                all_data['email'] = bidder_detail.email
                all_data['address_first'] = bidder_detail.address_first
                all_data['city'] = bidder_detail.city
                all_data['state'] = bidder_detail.state.state_name
                all_data['phone_no'] = bidder_detail.phone_no
                all_data['postal_code'] = bidder_detail.postal_code
                all_data['ip_address'] = bidder_detail.registration.ip_address
                all_data['bid_amount'] = bidder.bid_amount
                all_data['user_id'] = bidder.user_id
                # bid_limit = BidLimit.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, is_approved=2, status=1).last()
                # all_data['approval_limit'] = bid_limit.approval_limit
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_next_bid(obj):
        try:
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                return int(bidder.bid_amount) + int(bidder.auction.start_price)
            else:
                return obj.property_auction.first().start_price
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_total_bids(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidder(obj):
        try:
            return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_watcher(obj):
        try:
            return obj.property_watcher_property.filter(property=obj.id).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_price(obj):
        try:
            return obj.property_auction.first().reserve_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_met(obj):
        try:
            reserve_amount = obj.property_auction.first().reserve_amount
            max_bid_amount = obj.bid_property.filter(is_canceled=0).last().bid_amount
            if max_bid_amount >= reserve_amount:
                return "YES"
            else:
                return "NO"
        except Exception as exp:
            return "NO"

    @staticmethod
    def get_decreased_amount(obj):
        try:
            return obj.property_auction.first().insider_decreased_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_one_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_two_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_three_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_end_time(obj):
        try:
            return obj.property_auction.first().dutch_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_start_time(obj):
        try:
            return obj.property_auction.first().sealed_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_end_time(obj):
        try:
            return obj.property_auction.first().sealed_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_start_time(obj):
        try:
            return obj.property_auction.first().english_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_sealed_bid_amount(obj):
        try:
            return obj.bid_property.filter(user=obj.user_id, insider_auction_step=2, is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""


class SubdomainInlineBiddingMonitorSerializer(serializers.ModelSerializer):
    """
    SubdomainInlineBiddingMonitorSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    property_owner = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    current_bid = serializers.SerializerMethodField()
    high_bidder = serializers.SerializerMethodField()
    next_bid = serializers.SerializerMethodField()
    total_bids = serializers.SerializerMethodField()
    bidder = serializers.SerializerMethodField()
    watcher = serializers.SerializerMethodField()
    reserve_price = serializers.SerializerMethodField()
    reserve_met = serializers.SerializerMethodField()
    # high_bidder = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    decreased_amount = serializers.SerializerMethodField()
    round_one_winning_amount = serializers.SerializerMethodField()
    round_two_winning_amount = serializers.SerializerMethodField()
    round_three_winning_amount = serializers.SerializerMethodField()
    dutch_end_time = serializers.SerializerMethodField()
    sealed_start_time = serializers.SerializerMethodField()
    sealed_end_time = serializers.SerializerMethodField()
    english_start_time = serializers.SerializerMethodField()
    dutch_winning_user_id = serializers.SerializerMethodField()
    sealed_winning_user_id = serializers.SerializerMethodField()
    english_winning_user_id = serializers.SerializerMethodField()
    user_sealed_bid_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "status", "auction_data",
                  "current_bid", "high_bidder", "next_bid", "total_bids", "bidder", "watcher", "reserve_price",
                  "reserve_met", "property_owner", "read_by_auction_dashboard", "status_id", "domain", "domain_url",
                  "decreased_amount", "round_one_winning_amount", "round_two_winning_amount",
                  "round_three_winning_amount", "dutch_end_time", "sealed_start_time", "sealed_end_time", "english_start_time",
                  "dutch_winning_user_id", "sealed_winning_user_id", "english_winning_user_id", "user_sealed_bid_amount")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_owner(obj):
        try:
            all_data = {}
            all_data['first_name'] = obj.agent.first_name
            all_data['last_name'] = obj.agent.last_name
            all_data['company'] = obj.domain.domain_name
            all_data['phone_no'] = obj.agent.phone_no
            all_data['email'] = obj.agent.email
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_data(obj):
        try:
            auction = obj.property_auction.first()
            all_data = {
                "id": auction.id,
                "start_date": auction.start_date,
                "end_date": auction.end_date,
                "bid_increments": auction.bid_increments,
                "status": auction.status_id
            }
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_current_bid(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_high_bidder(obj):
        try:
            all_data = {}
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                if bidder.insider_auction_step == 2:
                    winner_step = obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first()
                    bidder = obj.bid_property.filter(id=winner_step.bid_id, is_canceled=0).last()
                high_bidder_id = bidder.user_id
                bidder_detail = BidRegistrationAddress.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, address_type__in=[2, 3], status=1).last()
                all_data['first_name'] = bidder_detail.first_name
                all_data['last_name'] = bidder_detail.last_name
                all_data['registration_id'] = bidder_detail.registration.registration_id
                all_data['email'] = bidder_detail.email
                all_data['address_first'] = bidder_detail.address_first
                all_data['city'] = bidder_detail.city
                all_data['state'] = bidder_detail.state.state_name
                all_data['phone_no'] = bidder_detail.phone_no
                all_data['postal_code'] = bidder_detail.postal_code
                all_data['ip_address'] = bidder_detail.registration.ip_address
                all_data['bid_amount'] = bidder.bid_amount
                all_data['user_id'] = bidder.user_id
                # bid_limit = BidLimit.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, is_approved=2, status=1).last()
                # all_data['approval_limit'] = bid_limit.approval_limit
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_next_bid(obj):
        try:
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                return int(bidder.bid_amount) + int(bidder.auction.start_price)
            else:
                return obj.property_auction.first().start_price
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_total_bids(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidder(obj):
        try:
            return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_watcher(obj):
        try:
            return obj.property_watcher_property.filter(property=obj.id).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_price(obj):
        try:
            return obj.property_auction.first().reserve_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_met(obj):
        try:
            reserve_amount = obj.property_auction.first().reserve_amount
            max_bid_amount = obj.bid_property.filter(is_canceled=0).last().bid_amount
            if max_bid_amount >= reserve_amount:
                return "YES"
            else:
                return "NO"
        except Exception as exp:
            return "NO"

    @staticmethod
    def get_decreased_amount(obj):
        try:
            return obj.property_auction.first().insider_decreased_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_one_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_two_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_round_three_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_end_time(obj):
        try:
            return obj.property_auction.first().dutch_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_start_time(obj):
        try:
            return obj.property_auction.first().sealed_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_end_time(obj):
        try:
            return obj.property_auction.first().sealed_end_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_start_time(obj):
        try:
            return obj.property_auction.first().english_start_time
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_sealed_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_english_winning_user_id(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=3, status=1).first().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_sealed_bid_amount(obj):
        try:
            return obj.bid_property.filter(user=obj.user_id, insider_auction_step=2, is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""


class TotalBidHistorySerializer(serializers.ModelSerializer):
    """
    TotalBidHistorySerializer
    """
    # bidder_detail = serializers.SerializerMethodField()
    is_last_bid = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        # fields = ("id", "bidder_detail", "bid_amount", "bid_date", "ip_address")
        fields = ("id", "bid_amount", "bid_date", "ip_address", "property", "is_last_bid")

    @staticmethod
    def get_bidder_detail(obj):
        try:
            register = BidRegistration.objects.filter(domain=obj.domain_id, property=obj.property_id, user=obj.user_id).first()
            if not register.property_yourself and register.user_type == 4:
                data = BidRegistrationAddress.objects.filter(registration__user=obj.user_id, registration__property=obj.property_id, address_type=3).first()
            else:
                data = BidRegistrationAddress.objects.filter(registration__user=obj.user_id, registration__property=obj.property_id, address_type=2).first()
            all_data = {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "phone_no": data.phone_no
            }
            return all_data
        except Exception as exp:
            return {}

    def get_is_last_bid(self, obj):
        try:
            last_bid = Bid.objects.filter(property=self.context, is_canceled=0, bid_type__in=[2, 3]).last()
            if obj.id == last_bid.id:
                return True
            else:
                return False
        except Exception as exp:
            return False










