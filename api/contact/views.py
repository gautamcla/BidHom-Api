# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.contact.models import *
from api.contact.serializers import *
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.db.models.functions import Lower
from api.packages.mail_service import send_email, compose_email, send_custom_email

class SuperAdminContactListingView(APIView):
    """
    Super admin contact us listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            site_id = None
            if "site_id" in data and type(data['site_id']) == list and len(data['site_id']) > 0:
                site_id = data['site_id']

            contact_us = ContactUs.objects
            if site_id is not None:
                contact_us = contact_us.filter(domain__in=site_id)
            
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                contact_us = contact_us.filter(status__in=data["status"])
            
            if "user_type" in data and type(data["user_type"]) == list and len(data["user_type"]) > 0:
                # convert user types in lower
                data['user_type'] =  [x.lower() for x in data['user_type']]
                contact_us = contact_us.annotate(user_type_lower=Lower('user_type')).filter(user_type_lower__in=data["user_type"])

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    contact_us = contact_us.filter(Q(id=search) | Q(phone_no__icontains=search))
                else:
                    contact_us = contact_us.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(user_type__icontains=search) | Q(full_name__icontains=search) | Q(domain__domain_name__icontains=search))
            total = contact_us.count()
            contact_us = contact_us.order_by("-id").only("id")[offset: limit]
            serializer = SuperAdminContactListingSerializer(contact_us, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminContactUsDetailApiView(APIView):
    """
    Super admin contact us detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "contact_id" in data and data['contact_id'] != "":
                contact_id = int(data['contact_id'])
            else:
                return Response(response.parsejson("contact_id is required", "", status=403))

            contact_us = ContactUs.objects.get(id=contact_id)
            serializer = SuperAdminContactUsDetailSerializer(contact_us)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontEnquiryApiView(APIView):
    """
    Front enquiry
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            data['status'] = 1
            serializer = FrontEnquirySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Your query send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChatToSellerApiView(APIView):
    """
    Chat to seller
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_data = PropertyListing.objects.filter(id=property_id, status=1).first()
                if property_data is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
                seller_id = property_data.agent_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))
            
            doc_ids = None
            if "doc_id_list" in data and type(data["doc_id_list"]) == list and len(data["doc_id_list"]) > 0:
                doc_ids = data['doc_id_list']

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required.", "", status=403))
            if seller_id == user_id:
                return Response(response.parsejson("You can't send message because you are owner of property.", "", status=403))

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(property=property_id) & Q(status=1) & Q(buyer=user_id)).first()
            if master is None:
                master = MasterChat()
                master.domain_id = site_id
                master.property_id = property_id
                master.buyer_id = user_id
                master.seller_id = seller_id
                master.added_by_id = user_id
                master.status_id = 1
                master.save()
                master_id = master.id
            else:
                master_id = master.id
            # -------------Save chat-----------
            chat = Chat()
            chat.master_id = master_id
            chat.message = message
            chat.sender_id = user_id
            chat.receiver_id = seller_id
            chat.status_id = 1
            chat.save()
            chat_id = chat.id

            # check if request have documents include 
            if doc_ids:
                for id in doc_ids:
                    chatDoc = ChatDocuments()
                    chatDoc.chat_id = chat_id
                    chatDoc.document_id = id
                    chatDoc.save()


            #--------Send Email-----------
            seller_detail = Users.objects.get(id=seller_id)
            seller_first_name = seller_detail.first_name
            seller_email = seller_detail.email
            buyer_detail = Users.objects.get(id=user_id)
            buyer_first_name = buyer_detail.first_name
            buyer_email = buyer_detail.email
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            domain_url = subdomain_url.replace("###", domain_name)+"chat"
            template_data = {"domain_id": site_id, "slug": "chat_with_agent"}
            #----------------send email buyer---------------------
            msg_text = 'Your message has been sent'
            extra_data = {"user_name": buyer_first_name, 'web_url': settings.FRONT_BASE_URL, 'property_image': data['property_image'], 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': data['message'], 'chat_link': domain_url, "domain_id": site_id, 'msg_text': msg_text}
            compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            #----------------send email to agent------------------
            domain_url = subdomain_url.replace("###", domain_name)+"/admin/chat/"
            msg_text = 'You have Received Message'
            extra_data = {"user_name": seller_first_name, 'web_url': settings.FRONT_BASE_URL, 'property_image': data['property_image'], 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': data['message'], 'chat_link': domain_url, "domain_id": site_id, 'msg_text': msg_text}
            compose_email(to_email=[seller_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Message send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserChatMasterListingApiView(APIView):
    """
    User chat master listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            last_msg_id = None
            if "last_msg_id" in data and data['last_msg_id'] != "":
                last_msg_id = int(data['last_msg_id'])

            msg_type = 'pre_msg'
            if "msg_type" in data and data['msg_type'] != "":
                msg_type = data['msg_type']

            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(buyer=user_id) & Q(status=1)).order_by("-chat_master__id").only("id")
            if "filter_data" in data and data['filter_data'] != "":
                filter_data = data['filter_data'].lower()
                if filter_data == "broker":
                    master = master.filter(seller__site=site_id)
                elif filter_data == "agent":
                    master = master.exclude(seller__site=site_id)

            if last_msg_id:
                if msg_type == 'pre_msg':
                    master = master.filter(Q(id__lt=last_msg_id))
                else:
                    master = master.filter(Q(id__gt=last_msg_id))
            total = master.count()
            master = master[offset:limit]
            serializer = UserChatMasterListingSerializer(master, many=True, context=user_id)
            all_data = {
                "data": serializer.data,
                "total": total,
                "page": page,
                "page_size": limit
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserChatListingApiView(APIView):
    """
    User chat listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "master_id" in data and data['master_id'] != "":
                master_id = int(data['master_id'])
            else:
                return Response(response.parsejson("master_id is required.", "", status=403))

            last_msg_id = None
            if "last_msg_id" in data and data['last_msg_id'] != "":
                last_msg_id = int(data['last_msg_id'])

            msg_type = 'pre_msg'
            if "msg_type" in data and data['msg_type'] != "":
                msg_type = data['msg_type']

            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            chat = Chat.objects.filter(Q(master=master_id) & Q(master__domain=site_id) & Q(master__status=1) & Q(status=1) & Q(master__buyer=user_id)).order_by("-id").only("id")
            if last_msg_id:
                if msg_type == 'pre_msg':
                    chat = chat.filter(Q(id__lt=last_msg_id))
                else:
                    chat = chat.filter(Q(id__gt=last_msg_id))
            total = chat.count()
            chat = reversed(chat[offset:limit])
            serializer = UserChatListingSerializer(chat, many=True, context=user_id)
            all_data = {
                "data": serializer.data,
                "total": total,
                "page": page,
                "page_size": limit
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserSendChatApiView(APIView):
    """
    User send chat
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "master_id" in data and data['master_id'] != "":
                master_id = int(data['master_id'])
                master = MasterChat.objects.filter(Q(id=master_id) & Q(buyer=user_id) & Q(status=1) & Q(domain=site_id)).first()
                if master is None:
                    return Response(response.parsejson("Conversation not active.", "", status=403))
                elif user_id == master.seller_id:
                    return Response(response.parsejson("Can't send message to self.", "", status=403))
                receiver_id = master.seller_id
            else:
                return Response(response.parsejson("master_id is required.", "", status=403))

            if "message" in data and data['message'] != "":
                message = data["message"]
            else:
                return Response(response.parsejson("message is required.", "", status=403))
            # -------------------Save chat----------------
            chat = Chat()
            chat.master_id = master_id
            chat.message = message
            chat.sender_id = user_id
            chat.receiver_id = receiver_id
            chat.status_id = 1
            chat.is_read = 0
            chat.save()
            chat_id = chat.id
            chat = Chat.objects.get(id=chat_id)
            serializer = UserSendChatDetailSerializer(chat)
            return Response(response.parsejson("Send successfully.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainChatMasterListingApiView(APIView):
    """
    Subdomain chat master listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_broker = 1
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    is_broker = None
                    users = Users.objects.filter(id=user_id, user_type=2, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            last_msg_id = None
            if "last_msg_id" in data and data['last_msg_id'] != "":
                last_msg_id = int(data['last_msg_id'])

            msg_type = 'pre_msg'
            if "msg_type" in data and data['msg_type'] != "":
                msg_type = data['msg_type']

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(status=1))
            if "filter_data" in data and data['filter_data'] != "":
                filter_data = data['filter_data'].lower()
                if filter_data == "buyer":
                    master = master.filter(Q(seller=user_id))
                elif filter_data == "broker":
                    master = master.filter(Q(seller__site=site_id) & Q(buyer=user_id))
            else:
                master = master.filter(Q(seller=user_id))

            # if is_broker is None:
            #     master = master.filter(Q(seller=user_id))
            if last_msg_id:
                if msg_type == 'pre_msg':
                    master = master.filter(Q(id__lt=last_msg_id))
                else:
                    master = master.filter(Q(id__gt=last_msg_id))

            total = master.count()
            master = master.order_by("-chat_master__id").only("id")[offset: limit]
            serializer = SubdomainChatMasterListingSerializer(master, many=True, context=user_id)
            all_data = {
                "data": serializer.data,
                "total": total,
                "page": page,
                "page_size": limit
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BrokerChatMasterListingApiView(APIView):
    """
    Broker chat master listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_broker = 1
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    is_broker = None
                    users = Users.objects.filter(id=user_id, user_type=2, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            last_msg_id = None
            if "last_msg_id" in data and data['last_msg_id'] != "":
                last_msg_id = int(data['last_msg_id'])

            msg_type = 'pre_msg'
            if "msg_type" in data and data['msg_type'] != "":
                msg_type = data['msg_type']

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(status=1))
            if "filter_data" in data and data['filter_data'] != "":
                filter_data = data['filter_data'].lower()
                if filter_data == "buyer":
                    master = master.filter(Q(seller=user_id))
                elif filter_data == "agent":
                    master = master.exclude(seller=user_id)

            if last_msg_id:
                if msg_type == 'pre_msg':
                    master = master.filter(Q(id__lt=last_msg_id))
                else:
                    master = master.filter(Q(id__gt=last_msg_id))

            total = master.count()
            master = master.order_by("-chat_master__id").only("id")[offset: limit]
            serializer = BrokerChatMasterListingSerializer(master, many=True, context=user_id)
            all_data = {
                "data": serializer.data,
                "total": total,
                "page": page,
                "page_size": limit
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainChatListingApiView(APIView):
    """
    Subdomain chat listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_broker = 1
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    is_broker = None
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, user_type=2, network_user__status=1, network_user__is_agent=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "master_id" in data and data['master_id'] != "":
                master_id = int(data['master_id'])
            else:
                return Response(response.parsejson("master_id is required.", "", status=403))

            last_msg_id = None
            if "last_msg_id" in data and data['last_msg_id'] != "":
                last_msg_id = int(data['last_msg_id'])

            msg_type = 'pre_msg'
            if "msg_type" in data and data['msg_type'] != "":
                msg_type = data['msg_type']

            chat = Chat.objects.filter(Q(master=master_id) & Q(master__domain=site_id) & Q(master__status=1) & Q(status=1)).order_by("-id").only("id")
            if is_broker is None:
                chat = chat.filter(Q(master__seller=user_id))

            if last_msg_id:
                if msg_type == 'pre_msg':
                    chat = chat.filter(Q(id__lt=last_msg_id))
                else:
                    chat = chat.filter(Q(id__gt=last_msg_id))

            total = chat.count()
            chat = reversed(chat[offset:limit])
            serializer = SubdomainChatListingSerializer(chat, many=True, context=user_id)
            all_data = {
                "data": serializer.data,
                "total": total,
                "page": page,
                "page_size": limit
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainSendChatApiView(APIView):
    """
    Subdomain send chat
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, user_type=2, network_user__status=1, network_user__is_agent=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "master_id" in data and data['master_id'] != "":
                master_id = int(data['master_id'])
                master = MasterChat.objects.filter(Q(id=master_id) & Q(domain=site_id) & Q(status=1) & Q(seller=user_id)).first()
                if master is None:
                    return Response(response.parsejson("Conversation not active.", "", status=403))
            else:
                return Response(response.parsejson("master_id is required.", "", status=403))

            if "message" in data and data['message'] != "":
                message = data["message"]
            else:
                return Response(response.parsejson("message is required.", "", status=403))
            # -------------------Save chat----------------
            chat = Chat()
            chat.master_id = master_id
            chat.message = message
            chat.sender_id = user_id
            chat.receiver_id = master.buyer_id
            chat.status_id = 1
            chat.save()
            chat_id = chat.id
            chat = Chat.objects.get(id=chat_id)
            serializer = ChatDetailSerializer(chat, context=user_id)
            return Response(response.parsejson("Send successfully.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChatToAgentApiView(APIView):
    """
    Chat to agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "agent_id" in data and data['agent_id'] != "":
                agent_id = int(data['agent_id'])
                users = Users.objects.filter(id=agent_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=agent_id, user_type=2, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("agent_id is required.", "", status=403))

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required.", "", status=403))
            if agent_id == user_id:
                return Response(response.parsejson("You can't send message to self.", "", status=403))

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(status=1) & Q(buyer=user_id) & Q(seller=agent_id) & Q(property__isnull=True)).first()
            if master is None:
                master = MasterChat()
                master.domain_id = site_id
                master.buyer_id = user_id
                master.seller_id = agent_id
                master.added_by_id = user_id
                master.status_id = 1
                master.save()
                master_id = master.id
            else:
                master_id = master.id
            # -------------Save chat-----------
            chat = Chat()
            chat.master_id = master_id
            chat.message = message
            chat.sender_id = user_id
            chat.receiver_id = agent_id
            chat.status_id = 1
            chat.save()
            #======================Send Email==========================
            buyer_detail = Users.objects.get(id=user_id)
            buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
            buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
            web_url = settings.FRONT_BASE_URL
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            domain_url = subdomain_url.replace("###", domain_name)+"chat"
            agent_detail = Users.objects.get(id=agent_id)
            agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
            agent_email = agent_detail.email if agent_detail.email is not None else ""
            try:
                # send email to buyer
                msg_text = 'Your message has been sent'
                template_data = {"domain_id": site_id, "slug": "chat_agent"}
                extra_data = {'user_name': buyer_name, 'web_url': web_url, 'chat_link': domain_url, 'chat_message': message, 'msg_text': msg_text}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data) 
            except Exception as e:
                pass
            if buyer_email.lower() != agent_email.lower():
                try:
                    #send email to agent
                    msg_text = 'You have Received Message'
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/chat/"
                    template_data = {"domain_id": site_id, "slug": "chat_agent"}
                    extra_data = {'user_name': agent_name, 'web_url': web_url, 'chat_link': domain_url, 'chat_message': message, 'msg_text': msg_text}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                except Exception as e:
                    pass
            return Response(response.parsejson("Message send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MarkChatReadApiView(APIView):
    """
    Mark chat read
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "master_id" in data and data['master_id'] != "":
                master_id = int(data['master_id'])
            else:
                return Response(response.parsejson("master_id is required.", "", status=403))

            Chat.objects.filter(master=master_id, receiver=user_id, status=1, is_read=0).update(is_read=1)
            return Response(response.parsejson("Chat mark as read successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChatToBuyerApiView(APIView):
    """
    Chat to buyer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_data = PropertyListing.objects.filter(id=property_id).first()
                if property_data is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "seller_id" in data and data['seller_id'] != "":
                seller_id = int(data['seller_id'])
                users = Users.objects.filter(id=seller_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=seller_id, user_type=2, network_user__domain=site_id, network_user__status=1, network_user__is_agent=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1, status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required.", "", status=403))

            master = MasterChat.objects.filter(Q(domain=site_id) & Q(property=property_id) & Q(status=1) & Q(buyer=user_id) & Q(seller=seller_id)).first()
            if master is None:
                master = MasterChat()
                master.domain_id = site_id
                master.property_id = property_id
                master.buyer_id = user_id
                master.seller_id = seller_id
                master.added_by_id = seller_id
                master.status_id = 1
                master.save()
                master_id = master.id
            else:
                master_id = master.id
            # -------------Save chat-----------
            chat = Chat()
            chat.master_id = master_id
            chat.message = message
            chat.sender_id = seller_id
            chat.receiver_id = user_id
            chat.status_id = 1
            chat.save()
            return Response(response.parsejson("Message send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))

