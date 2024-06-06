# -*- coding: utf-8 -*-
"""Contact Serializer

"""
from rest_framework import serializers
# from api.users.models import *
from api.payments.models import *
from api.contact.models import *
from django.db.models import F


class SuperAdminContactListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminContactListingSerializer
    """
    domain_name = serializers.CharField(source="domain.domain_name", read_only=True, default="")

    class Meta:
        model = ContactUs
        fields = ("id", "first_name", "last_name", "email", "phone_no", "user_type", "message", "added_on",
                  "domain_name")


class SuperAdminContactUsDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminContactUsDetailSerializer
    """

    class Meta:
        model = ContactUs
        fields = ("id", "message")


class FrontEnquirySerializer(serializers.ModelSerializer):
    """
    FrontEnquirySerializer
    """

    class Meta:
        model = ContactUs
        fields = "__all__"


class UserChatMasterListingSerializer(serializers.ModelSerializer):
    """
    UserChatMasterListingSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_date = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    property_data = serializers.SerializerMethodField()
    unread_msg_cnt = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = MasterChat
        fields = ("id", "image", "name", "last_message", "last_message_date", "email", "phone_no", "property_data",
                  "unread_msg_cnt", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.seller.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            # data = obj.seller.user_business_profile.filter(status=1).first()
            name = obj.seller.first_name
            return name + " " + obj.seller.last_name if obj.seller.last_name is not None and obj.seller.last_name != "" else name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_message(obj):
        try:
            return obj.chat_master.filter(status=1).last().message
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_message_date(obj):
        try:
            return obj.chat_master.filter(status=1).last().added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            # data = obj.seller.user_business_profile.filter(status=1).first()
            return obj.seller.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            # data = obj.seller.user_business_profile.filter(status=1).first()
            return obj.seller.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_data(obj):
        try:
            data = {}
            if obj.property_id is not None:
                data['id'] = obj.property.id
                data['name'] = obj.property.address_one + ", " + obj.property.city + ", " + obj.property.state.state_name + " " + obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    def get_unread_msg_cnt(self, obj):
        try:
            return obj.chat_master.filter(receiver=int(self.context), status=1, is_read=0).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.domain_id == obj.seller.site_id:
                return "Broker"
            else:
                return "Agent"
        except Exception as exp:
            return "Agent"


class UserChatListingSerializer(serializers.ModelSerializer):
    """
    UserChatMasterListingSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    message_date = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ("id", "image", "name", "email", "phone_no", "message", "message_date", "sender_id", "receiver_id",
                  "master_id", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.sender.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            # if obj.master.seller_id == obj.sender_id:
            #     data = obj.sender.user_business_profile.filter(status=1).first()
            # else:
            #     data = obj.sender
            data = obj.sender
            name = data.first_name
            return name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.sender.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.sender.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_message(obj):
        try:
            return obj.message
        except Exception as exp:
            return ""

    @staticmethod
    def get_message_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.master.seller_id == obj.sender_id:
                site_id = obj.master.seller.site_id
                if site_id == obj.master.domain_id:
                    return "Broker"
                else:
                    return "Agent"
            else:
                return "Buyer"
        except Exception as exp:
            return ""


class SubdomainChatMasterListingSerializer(serializers.ModelSerializer):
    """
    SubdomainChatMasterListingSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_date = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    property_data = serializers.SerializerMethodField()
    unread_msg_cnt = serializers.SerializerMethodField()
    is_my_chat = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = MasterChat
        fields = ("id", "image", "name", "last_message", "last_message_date", "email", "phone_no", "property_data",
                  "unread_msg_cnt", "is_my_chat", "buyer", "seller", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.buyer.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            data = obj.buyer
            name = data.first_name
            return name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_last_message(obj):
        try:
            return obj.chat_master.filter(status=1).last().message
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_message_date(obj):
        try:
            return obj.chat_master.filter(status=1).last().added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.buyer.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.buyer.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_data(obj):
        try:
            data = {}
            if obj.property_id is not None:
                data['id'] = obj.property.id
                data[
                    'name'] = obj.property.address_one + ", " + obj.property.city + ", " + obj.property.state.state_name + " " + obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_unread_msg_cnt(obj):
        try:
            return obj.chat_master.filter(receiver=int(obj.seller_id), status=1, is_read=0).count()
        except Exception as exp:
            return 0

    def get_is_my_chat(self, obj):
        try:
            if obj.seller_id == int(self.context):
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_user_type(obj):
        try:
            return "Buyer"
        except Exception as exp:
            return ""


class BrokerChatMasterListingSerializer(serializers.ModelSerializer):
    """
    BrokerChatMasterListingSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_date = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    property_data = serializers.SerializerMethodField()
    unread_msg_cnt = serializers.SerializerMethodField()
    is_my_chat = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = MasterChat
        fields = ("id", "image", "name", "last_message", "last_message_date", "email", "phone_no", "property_data",
                  "unread_msg_cnt", "is_my_chat", "user_type", "buyer", "seller")

    def get_image(self, obj):
        try:
            if int(self.context) == int(obj.seller_id):
                upload = UserUploads.objects.get(id=int(obj.buyer.profile_image))
                data = {
                    "doc_file_name": upload.doc_file_name,
                    "bucket_name": upload.bucket_name
                }
            else:
                upload = UserUploads.objects.get(id=int(obj.seller.profile_image))
                data = {
                    "doc_file_name": upload.doc_file_name,
                    "bucket_name": upload.bucket_name
                }
            return data
        except Exception as exp:
            return {}

    def get_name(self, obj):
        try:
            if int(self.context) == int(obj.seller_id):
                # data = obj.buyer.user_business_profile.filter(status=1).first()
                data = obj.buyer
                name = data.first_name
                name = name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
            else:
                # data = obj.seller.user_business_profile.filter(status=1).first()
                data = obj.seller
                name = data.first_name
                name = name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_message(obj):
        try:
            return obj.chat_master.filter(status=1).last().message
        except Exception as exp:
            return ""

    @staticmethod
    def get_last_message_date(obj):
        try:
            return obj.chat_master.filter(status=1).last().added_on
        except Exception as exp:
            return ""

    def get_email(self, obj):
        try:
            if int(self.context) == int(obj.seller_id):
                # data = obj.buyer.user_business_profile.filter(status=1).first()
                data = obj.buyer
            else:
                # data = obj.seller.user_business_profile.filter(status=1).first()
                data = obj.seller
            return data.email
        except Exception as exp:
            return ""

    def get_phone_no(self, obj):
        try:
            if int(self.context) == int(obj.seller_id):
                # data = obj.buyer.user_business_profile.filter(status=1).first()
                data = obj.buyer
            else:
                # data = obj.seller.user_business_profile.filter(status=1).first()
                data = obj.seller
            return data.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_data(obj):
        try:
            data = {}
            if obj.property_id is not None:
                data['id'] = obj.property.id
                data['name'] = obj.property.address_one + ", " + obj.property.city + ", " + obj.property.state.state_name + " " + obj.property.postal_code
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_unread_msg_cnt(obj):
        try:
            return obj.chat_master.filter(receiver=int(obj.seller_id), status=1, is_read=0).count()

        except Exception as exp:
            return 0

    def get_is_my_chat(self, obj):
        try:
            if obj.seller_id == int(self.context):
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_user_type(self, obj):
        try:
            if obj.seller_id == int(self.context):
                return "Buyer"
            else:
                return "Agent"
        except Exception as exp:
            return False


class SubdomainChatListingSerializer(serializers.ModelSerializer):
    """
    SubdomainChatListingSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    message_date = serializers.SerializerMethodField()
    chat_position = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ("id", "image", "name", "email", "phone_no", "message", "message_date", "sender_id", "receiver_id",
                  "master_id", "chat_position", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.sender.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            if obj.master.seller_id == obj.sender_id:
                # data = obj.sender.user_business_profile.filter(status=1).first()
                data = obj.sender
            else:
                data = obj.sender

            name = data.first_name
            return name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.sender.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.sender.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_message(obj):
        try:
            return obj.message
        except Exception as exp:
            return ""

    @staticmethod
    def get_message_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    def get_chat_position(self, obj):
        try:
            if int(obj.master.seller_id) == int(self.context):
                if obj.master.buyer_id == obj.sender_id:
                    return "left"
                else:
                    return "right"
            else:
                if obj.master.seller_id == obj.sender_id:
                    return "left"
                else:
                    return "right"
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            if obj.master.seller_id == obj.sender_id:
                site_id = obj.master.seller.site_id
                if site_id == obj.master.domain_id:
                    return "Broker"
                else:
                    return "Agent"
            else:
                return "Buyer"
        except Exception as exp:
            return ""


class ChatDetailSerializer(serializers.ModelSerializer):
    """
    ChatDetailSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    message_date = serializers.SerializerMethodField()
    chat_position = serializers.CharField(default="right")
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ("id", "image", "name", "email", "phone_no", "message", "message_date", "sender_id", "receiver_id",
                  "master_id", "chat_position", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.sender.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            # data = obj.sender.user_business_profile.filter(status=1).first()
            data = obj.sender
            name = data.first_name
            return name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.sender.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.sender.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_message(obj):
        try:
            return obj.message
        except Exception as exp:
            return ""

    @staticmethod
    def get_message_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    def get_user_type(self, obj):
        try:
            users = Users.objects.filter(site=obj.master.domain_id).first()
            if users is not None:
                if users.id == int(self.context):
                    return "Broker"
                else:
                    return "Agent"
            else:
                return ""
            # if obj.sender.site_id == obj.master.domain_id:
            #     return "Broker"
            # elif obj.master.property_id is not None and obj.master.property.agent_id == obj.sender_id:
            #     return "Agent"
            # else:
            #     return "Buyer"
        except Exception as exp:
            return ""


class UserSendChatDetailSerializer(serializers.ModelSerializer):
    """
    UserSendChatDetailSerializer
    """
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    message_date = serializers.SerializerMethodField()
    chat_position = serializers.CharField(default="right")
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ("id", "image", "name", "email", "phone_no", "message", "message_date", "sender_id", "receiver_id",
                  "master_id", "chat_position", "user_type")

    @staticmethod
    def get_image(obj):
        try:
            upload = UserUploads.objects.get(id=int(obj.sender.profile_image))
            data = {
                "doc_file_name": upload.doc_file_name,
                "bucket_name": upload.bucket_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_name(obj):
        try:
            # data = obj.sender.user_business_profile.filter(status=1).first()
            data = obj.sender
            name = data.first_name
            return name + " " + data.last_name if data.last_name is not None and data.last_name != "" else name
        except Exception as exp:
            return ""

    @staticmethod
    def get_email(obj):
        try:
            return obj.sender.email
        except Exception as exp:
            return ""

    @staticmethod
    def get_phone_no(obj):
        try:
            return obj.sender.phone_no
        except Exception as exp:
            return ""

    @staticmethod
    def get_message(obj):
        try:
            return obj.message
        except Exception as exp:
            return ""

    @staticmethod
    def get_message_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            return "Buyer"
        except Exception as exp:
            return ""

