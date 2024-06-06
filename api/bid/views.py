# -*- coding: utf-8 -*-
from re import escape
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.packages.common import *
from api.bid.models import *
from api.bid.serializers import *
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
from django.db.models import CharField
from django.db.models import Max, Min
from api.packages.mail_service import send_email, compose_email, send_custom_email
from django.db.models import F, Window
from django.db.models.functions.window import FirstValue, LastValue


class BidRegistrationDetailView(APIView):
    """
    Bid registration detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            user = Users.objects.get(id=user_id)
            serializer = BidRegistrationDetailSerializer(user, context=property_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidRegistrationView(APIView):
    """
    Bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                data['property'] = int(data['property_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            property_data = PropertyListing.objects.filter(id=property_id, domain=domain).first()
            if property_data is None:
                return Response(response.parsejson("Listing not available.", "", status=403))
            if property_data.agent_id == user_id:
                return Response(response.parsejson("You are owner of property.", "", status=403))
            if property_data.status_id != 1:
                return Response(response.parsejson("Listing not active.", "", status=403))

            if "address" in data and type(data['address']) == dict and len(data['address']) > 0:
                address = data['address']
                if "address_first" in address and address['address_first'] != "":
                    address_first = address['address_first']
                else:
                    return Response(response.parsejson("address->address_first is required", "", status=403))

                if "state" in address and address['state'] != "":
                    state = int(address['state'])
                else:
                    return Response(response.parsejson("address->state is required", "", status=403))

                if "postal_code" in address and address['postal_code'] != "":
                    postal_code = address['postal_code']
                else:
                    return Response(response.parsejson("address->postal_code is required", "", status=403))
            else:
                return Response(response.parsejson("address is required", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if "term_accepted" in data and data['term_accepted'] != "":
                if int(data['term_accepted']) == 1:
                    data['term_accepted'] = int(data['term_accepted'])
                else:
                    return Response(response.parsejson("term not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("term_accepted is required", "", status=403))

            if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
                uploads = data['uploads']
            else:
                return Response(response.parsejson("uploads is required", "", status=403))

            if "ip_address" in data and data['ip_address'] != "":
                ip_address = data['ip_address']
            else:
                return Response(response.parsejson("ip_address is required", "", status=403))

            # if "approval_limit" in data and data['approval_limit'] != "":
            #     approval_limit = int(data['approval_limit'])
            # else:
            #     return Response(response.parsejson("approval_limit is required", "", status=403))

            data['status'] = 1
            bid_registration = BidRegistration.objects.filter(domain=domain, user=user_id, property=property_id).exclude(status=5).first()
            if bid_registration is not None:
                return Response(response.parsejson("Already requested to registration.", "", status=403))
            with transaction.atomic():
                serializer = BidRegistrationSerializer(bid_registration, data=data)
                if serializer.is_valid():
                    registration_id = serializer.save()
                    registration_id = registration_id.id
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    for upload in uploads:
                        proof_funds = ProofFunds()
                        proof_funds.registration_id = registration_id
                        proof_funds.upload_id = upload
                        proof_funds.status_id = 1
                        proof_funds.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

                try:
                    profile_address = ProfileAddress.objects.filter(user=user_id, address_type=1, status=1).first()
                    if profile_address is None:
                        profile_address = ProfileAddress()
                        profile_address.user_id = user_id
                        profile_address.address_type_id = 1
                        profile_address.status_id = 1
                        profile_address.added_by_id = user_id
                        profile_address.updated_by_id = user_id
                    profile_address.address_first = address_first
                    profile_address.state_id = state
                    profile_address.postal_code = postal_code
                    profile_address.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

                # try:
                #     bid_limit = BidLimit()
                #     bid_limit.registration_id = registration_id
                #     bid_limit.approval_limit = approval_limit
                #     bid_limit.is_approved = 1
                #     bid_limit.status_id = 1
                #     bid_limit.save()
                # except Exception as exp:
                #     transaction.set_rollback(True)  # -----Rollback Transaction----
                #     return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Registration successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidsRegistrationView(APIView):
    """
    Bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                data['property'] = int(data['property_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            property_data = PropertyListing.objects.filter(id=property_id, domain=domain).first()
            property_auction = PropertyAuction.objects.filter(property=property_id, domain=domain).first()
            auction_id = None
            if property_auction is not None:
                auction_id = property_auction.id

            if property_data is None:
                return Response(response.parsejson("Listing not available.", "", status=403))
            if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 7:
                return Response(response.parsejson("This property not for auction", "", status=403))
            # if property_data.agent_id == user_id:
            #     return Response(response.parsejson("You are owner of property.", "", status=403))
            if property_data.status_id != 1:
                return Response(response.parsejson("Listing not active.", "", status=403))
            if not property_data.is_approved:
                return Response(response.parsejson("Listing not approved.", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if user_type == 2:  # -----------Buyer-------------
                if "working_with_agent" in data and data['working_with_agent'] != "":
                    working_with_agent = int(data['working_with_agent'])
                    if working_with_agent == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                else:
                    return Response(response.parsejson("working_with_agent is required", "", status=403))
            elif user_type == 4:  # -----------Agent-------------
                if "property_yourself" in data and data['property_yourself'] != "":
                    property_yourself = int(data['property_yourself'])
                    if property_yourself == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(
                                data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_seller_address" in data and type(data['buyer_seller_address']) == dict and len(data['buyer_seller_address']) > 0:
                            buyer_seller_address = data['buyer_seller_address']
                            if "first_name" in buyer_seller_address and buyer_seller_address['first_name'] != "":
                                buyer_seller_address_first_name = buyer_seller_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->first_name is required", "", status=403))

                            if "last_name" in buyer_seller_address and buyer_seller_address['last_name'] != "":
                                buyer_seller_address_last_name = buyer_seller_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->last_name is required", "", status=403))

                            if "email" in buyer_seller_address and buyer_seller_address['email'] != "":
                                buyer_seller_address_email = buyer_seller_address['email']
                            else:
                                return Response(response.parsejson("buyer_seller_address->email is required", "", status=403))

                            if "phone_no" in buyer_seller_address and buyer_seller_address['phone_no'] != "":
                                buyer_seller_address_phone_no = buyer_seller_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_seller_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_seller_address and buyer_seller_address['address_first'] != "":
                                buyer_seller_address_first = buyer_seller_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in buyer_seller_address and buyer_seller_address['city'] != "":
                                buyer_seller_address_city = buyer_seller_address['city']
                            else:
                                return Response(response.parsejson("buyer_seller_address->city is required", "", status=403))

                            if "state" in buyer_seller_address and buyer_seller_address['state'] != "":
                                buyer_seller_address_state = int(buyer_seller_address['state'])
                            else:
                                return Response(response.parsejson("buyer_seller_address->state is required", "", status=403))

                            if "postal_code" in buyer_seller_address and buyer_seller_address['postal_code'] != "":
                                buyer_seller_address_postal_code = buyer_seller_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_seller_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_seller_address is required", "", status=403))
                else:
                    return Response(response.parsejson("property_yourself is required", "", status=403))

            if "term_accepted" in data and data['term_accepted'] != "":
                if int(data['term_accepted']) == 1:
                    data['term_accepted'] = int(data['term_accepted'])
                else:
                    return Response(response.parsejson("term not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("term_accepted is required", "", status=403))

            if "age_accepted" in data and data['age_accepted'] != "":
                if int(data['age_accepted']) == 1:
                    data['age_accepted'] = int(data['age_accepted'])
                else:
                    return Response(response.parsejson("age not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("age_accepted is required", "", status=403))

            # if "correct_info" in data and data['correct_info'] != "":
            #     if int(data['correct_info']) == 1:
            #         data['correct_info'] = int(data['correct_info'])
            #     else:
            #         return Response(response.parsejson("User has not correct info.", "", status=403))
            # else:
            #     return Response(response.parsejson("correct_info is required", "", status=403))

            if "upload_pof" in data and data['upload_pof'] != "":
                upload_pof = int(data['upload_pof'])
            else:
                return Response(response.parsejson("upload_pof is required", "", status=403))

            uploads = None
            if upload_pof == 1:
                data['reason_for_not_upload'] = None
                if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
                    uploads = data['uploads']
                else:
                    return Response(response.parsejson("uploads is required", "", status=403))
            else:
                if "reason_for_not_upload" in data and data['reason_for_not_upload'] != "":
                    reason_for_not_upload = data['reason_for_not_upload']
                else:
                    return Response(response.parsejson("reason_for_not_upload is required", "", status=403))

            if "ip_address" in data and data['ip_address'] != "":
                ip_address = data['ip_address']
            else:
                return Response(response.parsejson("ip_address is required", "", status=403))

            data['status'] = 1
            bid_registration = BidRegistration.objects.filter(domain=domain, user=user_id, property=property_id, status=1).first()
            if bid_registration is not None:
                return Response(response.parsejson("Already requested to registration.", "", status=403))

            # -----------------------Check auto approve--------------
            property_settings = PropertySettings.objects.filter(domain=domain, property=property_id, is_broker=0, is_agent=0, status=1).first()
            auto_approve = None
            approval_limit = None
            if property_settings is not None:
                if property_settings.auto_approval == 1:
                    auto_approve = True
                    approval_limit = property_settings.bid_limit
                    data['is_reviewed'] = 1
                    data['is_approved'] = 2
                    data['seller_comment'] = "Auto approve"
            else:
                property_settings = PropertySettings.objects.filter(domain=domain, is_agent=1, is_broker=0, status=1).first()
                if property_settings is not None:
                    if property_settings.auto_approval == 1:
                        auto_approve = True
                        approval_limit = property_settings.bid_limit
                        data['is_reviewed'] = 1
                        data['is_approved'] = 2
                        data['seller_comment'] = "Auto approve"
                else:
                    property_settings = PropertySettings.objects.filter(domain=domain, is_broker=1, is_agent=0, status=1).first()
                    if property_settings is not None and property_settings.auto_approval == 1:
                        auto_approve = True
                        approval_limit = property_settings.bid_limit
                        data['is_reviewed'] = 1
                        data['is_approved'] = 2
                        data['seller_comment'] = "Auto approve"

            registration_id = unique_registration_id()  # Get unique registration id
            if registration_id:
                data['registration_id'] = registration_id
            else:
                return Response(response.parsejson("Registration id not generated.", "", status=403))
            with transaction.atomic():
                serializer = BidRegistrationSerializer(data=data)
                if serializer.is_valid():
                    registration_id = serializer.save()
                    registration_id = registration_id.id
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                if auto_approve is not None:
                    try:
                        bid_limit = BidLimit()
                        bid_limit.registration_id = registration_id
                        bid_limit.status_id = 1
                        bid_limit.approval_limit = approval_limit
                        bid_limit.is_approved = 2
                        bid_limit.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))
                try:
                    if uploads is not None and len(uploads) > 0:
                        for upload in uploads:
                            proof_funds = ProofFunds()
                            proof_funds.registration_id = registration_id
                            proof_funds.upload_id = upload
                            proof_funds.status_id = 1
                            proof_funds.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
                registration_data = {}
                if user_type == 2:
                    registration_data['first_name'] = buyer_address['first_name']
                    registration_data['last_name'] = buyer_address['last_name']
                    registration_data['email'] = buyer_address['email']
                    registration_data['phone_no'] = buyer_address['phone_no']
                    if working_with_agent == 1:
                        agent_address['address_type'] = 1
                        agent_address['registration'] = registration_id
                        agent_address['status'] = 1
                        agent_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=agent_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                        buyer_address['address_type'] = 2
                        buyer_address['registration'] = registration_id
                        buyer_address['status'] = 1
                        buyer_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=buyer_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                    else:
                        buyer_address['address_type'] = 2
                        buyer_address['registration'] = registration_id
                        buyer_address['status'] = 1
                        buyer_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=buyer_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                elif user_type == 4:
                    if property_yourself == 1:
                        registration_data['first_name'] = buyer_address['first_name']
                        registration_data['last_name'] = buyer_address['last_name']
                        registration_data['email'] = buyer_address['email']
                        registration_data['phone_no'] = buyer_address['phone_no']

                        buyer_address['address_type'] = 2
                        buyer_address['registration'] = registration_id
                        buyer_address['status'] = 1
                        buyer_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=buyer_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                        agent_address['address_type'] = 1
                        agent_address['registration'] = registration_id
                        agent_address['status'] = 1
                        agent_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=agent_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                    else:
                        registration_data['first_name'] = buyer_seller_address['first_name']
                        registration_data['last_name'] = buyer_seller_address['last_name']
                        registration_data['email'] = buyer_seller_address['email']
                        registration_data['phone_no'] = buyer_seller_address['phone_no']

                        buyer_seller_address['address_type'] = 3
                        buyer_seller_address['registration'] = registration_id
                        buyer_seller_address['status'] = 1
                        buyer_seller_address['auction'] = auction_id
                        serializer = BidRegistrationAddressSerializer(data=buyer_seller_address)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    bid_registration_data = BidRegistration.objects.get(id=registration_id)
                    serializer = BidRegistrationSerializer(bid_registration_data, data=registration_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

            try:
                property_detail = PropertyListing.objects.get(id=property_id)
                agent_detail = property_detail.agent
                agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                agent_email = agent_detail.email if agent_detail.email is not None else ""
                agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                buyer_detail = Users.objects.get(id=user_id)
                buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                broker_detail = Users.objects.get(site_id=domain)
                broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                broker_email = broker_detail.email if broker_detail.email is not None else ""
                broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                property_address = property_detail.address_one if property_detail.address_one is not None else ""
                property_city = property_detail.city if property_detail.city is not None else ""
                property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                image = ''
                bucket_name = ''
                if upload is not None:
                    image = upload.upload.doc_file_name if upload.upload.doc_file_name is not None else ""
                    bucket_name = upload.upload.bucket_name if upload.upload.bucket_name is not None else ""
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                #=========================Send email to buyer====================
                template_data = {"domain_id": domain, "slug": "bid_registration"}
                domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(property_id)
                extra_data = {'user_name': buyer_name,
                            'web_url': web_url,
                            'property_image': image_url,
                            'property_address': property_address,
                            'property_city': property_city,
                            'property_state': property_state,
                            'prop_link': domain_url,
                            "domain_id": domain,
                            'agent_name': agent_name,
                            'agent_email': agent_email,
                            'agent_phone': phone_format(agent_phone)
                        }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                #========================Send email to agent=========================
                if agent_email.lower() != buyer_email.lower():
                    template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                    extra_data = {'user_name': agent_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #========================Send email to broker========================
                if broker_email.lower() != agent_email.lower():
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                    template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                    extra_data = {'user_name': broker_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                if auto_approve:
                    template_data = {"domain_id": domain, "slug": "bid_registration_approval"}
                    domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(property_id)
                    extra_data = {'user_name': buyer_name, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, 'domain_id': domain, 'status': 'approved'}
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            except Exception as e:
                pass

            try:
                prop_name = property_data.address_one if property_data.address_one else property_data.id
                #  add notfification to buyer
                content = "Your registration has been sent!! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain,
                    "Bid Registration",
                    content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    property_id=property_id
                )
                if user_id != property_data.agent_id:
                    #  add notfification to seller/agent
                    content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration",
                        content,
                        user_id=property_data.agent_id,
                        added_by=property_data.agent_id,
                        notification_for=2,
                        property_id=property_id
                    )
                # if user_id != property_data.agent_id and user_id != broker_detail.id:
                if property_data.agent_id != broker_detail.id:
                    content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration",
                        content,
                        user_id=broker_detail.id,
                        added_by=broker_detail.id,
                        notification_for=2,
                        property_id=property_id
                    )
                # send approval notif if auto approval on
                if auto_approve:
                    content = "Your registration has been approved! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration",
                        content,
                        user_id=user_id,
                        added_by=user_id,
                        notification_for=1,
                        property_id=property_id
                    )

            except Exception as e:
                pass
            registration_data = {"registration_id": registration_id}
            return Response(response.parsejson("Registration successfully.", registration_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidRegistrationProofUploadView(APIView):
    """
    Bid registration proof upload
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("registration_id is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "upload_pof" in data and data['upload_pof'] != "":
                upload_pof = int(data['upload_pof'])
            else:
                return Response(response.parsejson("upload_pof is required", "", status=403))

            uploads = None
            reason_for_not_upload = None
            if upload_pof == 1:
                if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
                    uploads = data['uploads']
                else:
                    return Response(response.parsejson("uploads is required", "", status=403))
            else:
                if "reason_for_not_upload" in data and data['reason_for_not_upload'] != "":
                    reason_for_not_upload = data['reason_for_not_upload']
                else:
                    return Response(response.parsejson("reason_for_not_upload is required", "", status=403))

            # uploads = None
            # if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
            #     uploads = data['uploads']

            bid_registration = BidRegistration.objects.filter(id=registration_id, domain=domain, user=user_id).first()
            if bid_registration is None:
                return Response(response.parsejson("You can't update.", "", status=403))

            bid_registration.upload_pof = upload_pof
            bid_registration.reason_for_not_upload = reason_for_not_upload
            bid_registration.save()

            try:
                if uploads is not None and len(uploads) > 0:
                    for upload in uploads:
                        proof_funds = ProofFunds()
                        proof_funds.registration_id = registration_id
                        proof_funds.upload_id = upload
                        proof_funds.status_id = 1
                        proof_funds.save()
            except Exception as exp:
                return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Proof of fund updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainBidRegistrationListingView(APIView):
    """
    Subdomain bid registration listing
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=site_id).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # bid_registration = BidRegistration.objects.annotate(Count('id')).filter(Q(domain=site_id) & Q(status=1) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id))).exclude(property__status__in=[5])
            bid_registration = BidRegistration.objects.filter(Q(domain=site_id) & Q(status=1) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id))).exclude(property__status__in=[5])
            # -------Filter-------
            if "asset_type" in data and data['asset_type'] != "":
                asset_type = int(data['asset_type'])
                bid_registration = bid_registration.filter(property__property_asset=asset_type)

            property_address = {}
            property_image = {}
            property_id = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id).first()
                if property_listing is not None:
                    property_address['address_one'] = property_listing.address_one
                    property_address['city'] = property_listing.city
                    property_address['state'] = property_listing.state.state_name
                    property_address['postal_code'] = property_listing.postal_code
                    image = property_listing.property_uploads_property.filter(upload_type=1).first()
                    if image is not None:
                        property_image = {"image": image.upload.doc_file_name, "bucket_name": image.upload.bucket_name}

                bid_registration = bid_registration.filter(property=property_id)

            if "filter_data" in data and data['filter_data'] != "":
                if int(data['filter_data']) == 1:  # ----------For pending------------
                    bid_registration = bid_registration.filter(is_approved=1)
                elif int(data['filter_data']) == 2:  # ----------For approved------------
                    bid_registration = bid_registration.filter(is_approved=2)
                elif int(data['filter_data']) == 3:  # ----------For rejected------------
                    bid_registration = bid_registration.filter(is_approved=3)
                elif int(data['filter_data']) == 4:  # ----------For reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=1)
                elif int(data['filter_data']) == 5:  # ----------For not reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=0)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                # if search.isdigit():
                #     bid_registration = bid_registration.filter(Q(id=search) | Q(bid_registration_address_registration__phone_no__icontains=search))
                # else:
                #     if property_id is None:
                #         bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('bid_registration_address_registration__first_name', V(' '), 'bid_registration_address_registration__last_name')).filter(Q(bid_registration_address_registration__first_name__icontains=search) | Q(full_name__icontains=search) | Q(bid_registration_address_registration__phone_no__icontains=search) | Q(bid_registration_address_registration__email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(bid_registration_address_registration__city__icontains=search))
                #     else:
                #         bid_registration = bid_registration.annotate(full_name=Concat('bid_registration_address_registration__first_name', V(' '), 'bid_registration_address_registration__last_name')).filter(Q(bid_registration_address_registration__first_name__icontains=search) | Q(full_name__icontains=search) | Q(bid_registration_address_registration__phone_no__icontains=search) | Q(bid_registration_address_registration__email__icontains=search) | Q(ip_address__icontains=search))
                if search.isdigit():
                    bid_registration = bid_registration.filter(Q(id=search) | Q(phone_no__icontains=search))
                else:
                    if property_id is None:
                        bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(full_name__icontains=search) | Q(phone_no__icontains=search) | Q(email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(user__user_type__user_type__icontains=search))
                    else:
                        bid_registration = bid_registration.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(full_name__icontains=search) | Q(phone_no__icontains=search) | Q(email__icontains=search) | Q(ip_address__icontains=search) | Q(user__user_type__user_type__icontains=search))

            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = SubdomainBidRegistrationListingSerializer(bid_registration, many=True)
            all_data = {
                'data': serializer.data,
                "total": total,
                "property_address": property_address,
                "property_image": property_image
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainBidRegistrationDetailView(APIView):
    """
    Subdomain bid registration detail
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

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("registration_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=site_id).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.get(Q(id=registration_id) & Q(domain=site_id) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)))
            serializer = SubdomainBidRegistrationDetailSerializer(bid_registration)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateSubdomainBidRegistrationView(APIView):
    """
    Update subdomain bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            # if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
            #     uploads = data['uploads']
            # else:
            #     return Response(response.parsejson("uploads is required", "", status=403))

            if "is_reviewed" in data and data['is_reviewed'] != "":
                is_reviewed = data['is_reviewed']
            else:
                return Response(response.parsejson("is_reviewed is required", "", status=403))

            if "is_approved" in data and data['is_approved'] != "":
                is_approved = int(data['is_approved'])
            else:
                return Response(response.parsejson("is_approved is required", "", status=403))

            seller_comment = None
            if "seller_comment" in data and data['seller_comment'] != "":
                seller_comment = data['seller_comment']

            if "approval_limit" in data and data['approval_limit'] != "":
                approval_limit = data['approval_limit']
            else:
                return Response(response.parsejson("approval_limit is required", "", status=403))

            with transaction.atomic():
                try:
                    bid_registration = BidRegistration.objects.filter(Q(id=registration_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id))).first()
                    if bid_registration is None:
                        return Response(response.parsejson("You have not permission to update.", "", status=403))

                    current_status = bid_registration.is_approved
                    bid_registration.is_reviewed = is_reviewed
                    bid_registration.is_approved = is_approved
                    bid_registration.seller_comment = seller_comment
                    bid_registration.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

                # try:
                #     ProofFunds.objects.filter(registration=registration_id).delete()
                #     for upload in uploads:
                #         proof_funds = ProofFunds()
                #         proof_funds.registration_id = registration_id
                #         proof_funds.upload_id = upload
                #         proof_funds.status_id = 1
                #         proof_funds.save()
                # except Exception as exp:
                #     transaction.set_rollback(True)  # -----Rollback Transaction----
                #     return Response(response.parsejson(str(exp), exp, status=403))

                try:
                    bid_limit = BidLimit.objects.filter(registration=registration_id, status=1).last()
                    if bid_limit is None:
                        bid_limit = BidLimit()
                        bid_limit.registration_id = registration_id
                        bid_limit.status_id = 1
                    elif bid_limit is not None and int(bid_limit.approval_limit) != int(approval_limit):
                        bid_limit = BidLimit()
                        bid_limit.registration_id = registration_id
                        bid_limit.status_id = 1

                    bid_limit.approval_limit = approval_limit
                    bid_limit.is_approved = is_approved
                    bid_limit.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            
            property_data = PropertyListing.objects.get(id=bid_registration.property_id)
            property_address = property_data.address_one if property_data.address_one is not None else ""
            property_city = property_data.city if property_data.city is not None else ""
            property_state = property_data.state.state_name if property_data.state.state_name is not None else ""
            upload = PropertyUploads.objects.filter(property=bid_registration.property_id, upload_type=1).first()
            web_url = settings.FRONT_BASE_URL
            image_url = web_url+'/static/admin/images/property-default-img.png'
            image = ''
            bucket_name = ''
            if upload is not None:
                image = upload.upload.doc_file_name if upload.upload.doc_file_name is not None else ""
                bucket_name = upload.upload.bucket_name if upload.upload.bucket_name is not None else ""
                image_url = settings.AWS_URL+bucket_name+'/'+image
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            user_data = Users.objects.get(id=bid_registration.user_id)
            user_name = user_data.first_name if user_data.first_name else ""  
            user_email = user_data.email if user_data.email else ""
            #send email to buyer for bidding approval status
            try:
                template_data = {"domain_id": domain, "slug": "bid_registration_approval"}
                domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(bid_registration.property_id)
                if "is_approved" in data and data['is_approved'] != "":
                    if int(data['is_approved']) == 1:
                        status = 'pending'
                    elif int(data['is_approved']) == 2:
                        status = 'approved'
                    elif int(data['is_approved']) == 3:
                        status = 'declined'
                    elif int(data['is_approved']) == 4:
                        status = 'not interested'
                    else:
                        status = ''
                extra_data = {
                    'user_name': user_name,
                    'property_image': image_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'dashboard_link': domain_url,
                    'domain_id': domain,
                    'status': status
                    }
                compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            except Exception as e:
                pass
              
            try:
                prop_name = bid_registration.property.address_one if bid_registration.property.address_one else bid_registration.property.id
                # notify buyer for approval
                if is_approved == 1:
                    status = 'pending'
                elif is_approved == 2:
                    status = 'approved'
                elif is_approved == 3:
                    status = 'declined'
                elif is_approved == 4:
                    status = 'not interested'
                else:
                    status = ''
                if status and is_approved in [1,2,3] and int(current_status) != is_approved:
                    content = "Your registration has been "+ status +"! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration Approval",
                        content,
                        user_id=bid_registration.user_id,
                        added_by=bid_registration.user_id,
                        notification_for=1,
                        property_id=bid_registration.property_id
                    )
            except Exception as e:
                print(e)
            all_data = {"property_id": bid_registration.property_id, "auction_type": bid_registration.property.sale_by_type_id}
            return Response(response.parsejson("Updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainDeleteBidRegistrationView(APIView):
    """
    Subdomain delete bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            bid_registration = BidRegistration.objects.filter(Q(id=registration_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(status=1)).first()
            if bid_registration is None:
                return Response(response.parsejson("Registration not exist.", "", status=403))
            property_id = bid_registration.property_id
            auction_type = bid_registration.property.sale_by_type_id
            bid_count = Bid.objects.filter(domain=domain, property=bid_registration.property_id, user=bid_registration.user_id).count()
            if bid_count > 0:
                return Response(response.parsejson("Can't inactive because buyer placed a bid.", "", status=403))
            with transaction.atomic():
                try:
                    bid_registration = BidRegistration.objects.filter(Q(id=registration_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id))).update(status_id=2)
                    # if bid_registration is None:
                    #     return Response(response.parsejson("You have not permission to delete.", "", status=403))
                    # bid_registration.status_id = 5
                    # bid_registration.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            property_auction = PropertyAuction.objects.filter(property=property_id).last()
            all_data = {"property_id": property_id, "auction_type": auction_type, "auction_id": property_auction.id}
            return Response(response.parsejson("Deleted successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainDeleteRegistrationUploadView(APIView):
    """
    Subdomain delete registration upload
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            registration_id = None
            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            with transaction.atomic():
                try:
                    if registration_id is not None:
                        bid_registration = BidRegistration.objects.filter(Q(id=registration_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id))).first()
                        if bid_registration is None:
                            return Response(response.parsejson("You have not permission to delete.", "", status=403))
                        ProofFunds.objects.filter(registration=registration_id, upload=upload_id).delete()
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminDeleteRegistrationUploadView(APIView):
    """
    Super admin delete registration upload
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            with transaction.atomic():
                try:
                    bid_registration = BidRegistration.objects.filter(Q(id=registration_id)).first()
                    if bid_registration is None:
                        return Response(response.parsejson("You have not permission to delete.", "", status=403))
                    ProofFunds.objects.filter(registration=registration_id, upload=upload_id).delete()
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainBidRegistrationSuggestionView(APIView):
    """
    Subdomain bid registration suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1,
                                                              is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised  user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))

            searched_data = []
            bid_registration = BidRegistration.objects.annotate(data=Concat('view_bid_registration_address_registration__first_name', V(' '), 'view_bid_registration_address_registration__last_name')).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('domain__domain_name')).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('view_bid_registration_address_registration__email')).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('view_bid_registration_address_registration__phone_no')).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = ViewBidRegistrationAddress.objects.annotate(data=F('city')).filter(Q(registration__domain=domain) & (Q(registration__property__agent=user_id) | Q(registration__property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('ip_address')).filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminBidRegistrationListingView(APIView):
    """
    Super admin bid registration listing
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
            
            listing_id = None
            if "listing_id" in data and data['listing_id']:
                listing_id = int(data['listing_id'])

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.annotate(Count("id")).filter(status=1)
            # -------Filter-------
            if "asset_type" in data and type(data['asset_type']) == list and len(data['asset_type']) > 0:
                asset_type = data['asset_type']
                bid_registration = bid_registration.filter(property__property_asset__in=asset_type)
            if site_id is not None:
                bid_registration = bid_registration.filter(Q(domain__in=site_id))
            
            if listing_id:
                bid_registration = bid_registration.filter(property=listing_id)

            if "filter_data" in data and data['filter_data'] != "":
                if int(data['filter_data']) == 1:  # ----------For pending------------
                    bid_registration = bid_registration.filter(is_approved=1)
                elif int(data['filter_data']) == 2:  # ----------For approved------------
                    bid_registration = bid_registration.filter(is_approved=2)
                elif int(data['filter_data']) == 3:  # ----------For rejected------------
                    bid_registration = bid_registration.filter(is_approved=3)
                elif int(data['filter_data']) == 4:  # ----------For reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=1)
                elif int(data['filter_data']) == 5:  # ----------For not reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=0)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    bid_registration = bid_registration.filter(Q(id=search) | Q(phone_no__icontains=search))
                else:
                    bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(full_name__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(phone_no__icontains=search) | Q(email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(property__address_one__icontains=search))
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = SuperAdminBidRegistrationListingSerializer(bid_registration, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminBidRegistrationDetailView(APIView):
    """
    Super admin bid registration detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("registration_id is required", "", status=403))

            bid_registration = BidRegistration.objects.get(id=registration_id)
            serializer = SuperAdminBidRegistrationDetailNewSerializer(bid_registration)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateSuperAdminBidRegistrationView(APIView):
    """
    Update super admin bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
            #     uploads = data['uploads']
            # else:
            #     return Response(response.parsejson("uploads is required", "", status=403))

            if "is_reviewed" in data and data['is_reviewed'] != "":
                is_reviewed = data['is_reviewed']
            else:
                return Response(response.parsejson("is_reviewed is required", "", status=403))

            if "is_approved" in data and data['is_approved'] != "":
                is_approved = int(data['is_approved'])
            else:
                return Response(response.parsejson("is_approved is required", "", status=403))

            seller_comment = None
            if "seller_comment" in data and data['seller_comment'] != "":
                seller_comment = data['seller_comment']

            if "approval_limit" in data and data['approval_limit'] != "":
                approval_limit = data['approval_limit']
            else:
                return Response(response.parsejson("approval_limit is required", "", status=403))

            with transaction.atomic():
                try:
                    bid_registration = BidRegistration.objects.get(Q(id=registration_id))
                    current_status = bid_registration.is_approved
                    bid_registration.is_reviewed = is_reviewed
                    bid_registration.is_approved = is_approved
                    bid_registration.seller_comment = seller_comment
                    bid_registration.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

                # try:
                #     ProofFunds.objects.filter(registration=registration_id).delete()
                #     for upload in uploads:
                #         proof_funds = ProofFunds()
                #         proof_funds.registration_id = registration_id
                #         proof_funds.upload_id = upload
                #         proof_funds.status_id = 1
                #         proof_funds.save()
                # except Exception as exp:
                #     transaction.set_rollback(True)  # -----Rollback Transaction----
                #     return Response(response.parsejson(str(exp), exp, status=403))

                try:
                    bid_limit = BidLimit.objects.filter(registration=registration_id, status=1).last()
                    if bid_limit is None:
                        bid_limit = BidLimit()
                        bid_limit.registration_id = registration_id
                        bid_limit.is_approved = 2
                        bid_limit.status_id = 1
                    elif bid_limit is not None and int(bid_limit.approval_limit) != int(approval_limit):
                        bid_limit = BidLimit()
                        bid_limit.registration_id = registration_id
                        bid_limit.is_approved = 2
                        bid_limit.status_id = 1

                    bid_limit.approval_limit = approval_limit
                    bid_limit.is_approved = 2
                    bid_limit.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            
            try:
                prop_name = bid_registration.property.address_one if bid_registration.property.address_one else bid_registration.property.id
                property_address = bid_registration.property.address_one if bid_registration.property.address_one is not None else ""
                property_city = bid_registration.property.city if bid_registration.property.city is not None else ""
                property_state = bid_registration.property.state.state_name if bid_registration.property.state.state_name is not None else ""
                upload = PropertyUploads.objects.filter(property=bid_registration.property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                image = ''
                bucket_name = ''
                if upload is not None:
                    image = upload.upload.doc_file_name if upload.upload.doc_file_name is not None else ""
                    bucket_name = upload.upload.bucket_name if upload.upload.bucket_name is not None else ""
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                domain_name = bid_registration.domain.domain_name
                user_name = bid_registration.user.first_name if bid_registration.user.first_name else ""  
                user_email = bid_registration.user.email if bid_registration.user.email else ""
                template_data = {"domain_id": bid_registration.domain_id, "slug": "bid_registration_approval"}
                domain_url = settings.SUBDOMAIN_URL.replace("###", domain_name)+"asset-details/?property_id="+str(bid_registration.property_id)
                # notify buyer for approval
                if is_approved == 1:
                        status = 'pending'
                elif is_approved == 2:
                    status = 'approved'
                elif is_approved == 3:
                    status = 'declined'
                elif is_approved == 4:
                    status = 'not interested'
                else:
                    status = ''
                if status and is_approved in [1, 2,3] and int(current_status) != is_approved:
                    content = "Your registration has been " + status + "! <span>[" + prop_name + "]</span>"
                    add_notification(
                        bid_registration.domain_id,
                        "Bid Registration Approval",
                        content,
                        user_id=bid_registration.user_id,
                        added_by=user_id,
                        notification_for=1,
                        property_id=bid_registration.property_id
                    )

                    extra_data = {
                    'user_name': user_name,
                    'property_image': image_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'dashboard_link': domain_url,
                    'domain_id': bid_registration.domain_id,
                    'status': status
                    }
                    compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            except Exception as e:
                print(e)
            return Response(response.parsejson("Updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainPropertyRegistrationSuggestionView(APIView):
    """
    Subdomain property registration suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1,
                                                              is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised  user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = data['property_id']
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))

            searched_data = []
            bid_registration = BidRegistration.objects.annotate(data=Concat('view_bid_registration_address_registration__first_name', V(' '), 'view_bid_registration_address_registration__last_name')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('domain__domain_name')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('view_bid_registration_address_registration__email')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('view_bid_registration_address_registration__phone_no')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('view_bid_registration_address_registration__city')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            bid_registration = BidRegistration.objects.annotate(data=F('ip_address')).filter(Q(property=property_id) & Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)) & Q(data__icontains=search)).values("data")
            searched_data = searched_data + list(bid_registration)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidRegistrationListingView(APIView):
    """
    Bid registration listing
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).exclude(user_type=3).first()
                # user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.filter(Q(domain=site_id) & Q(user=user_id)).exclude(Q(status__in=[2, 5]) | Q(property__status=5) | Q(property__sale_by_type=2))
            # -------Filter-------
            if "asset_type" in data and data['asset_type'] != "":
                asset_type = int(data['asset_type'])
                bid_registration = bid_registration.filter(property__property_asset=asset_type)

            if "filter_data" in data and data['filter_data'] != "":
                if int(data['filter_data']) == 1:  # ----------For pending------------
                    bid_registration = bid_registration.filter(is_approved=1)
                elif int(data['filter_data']) == 2:  # ----------For approved------------
                    bid_registration = bid_registration.filter(is_approved=2)
                elif int(data['filter_data']) == 3:  # ----------For rejected------------
                    bid_registration = bid_registration.filter(is_approved=3)
                elif int(data['filter_data']) == 4:  # ----------For reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=1)
                elif int(data['filter_data']) == 5:  # ----------For not reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=0)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    bid_registration = bid_registration.filter(Q(id=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search))
                else:
                    bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('view_bid_registration_address_registration__first_name', V(' '), 'view_bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(view_bid_registration_address_registration__first_name__icontains=search) | Q(view_bid_registration_address_registration__last_name__icontains=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search) | Q(view_bid_registration_address_registration__email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(view_bid_registration_address_registration__city__icontains=search))
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = BidRegistrationListingSerializer(bid_registration, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainBidHistoryView(APIView):
    """
    Subdomain bid history
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            register_user = None
            if "register_user" in data and data['register_user'] != "":
                register_user = int(data['register_user'])

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # bid = Bid.objects.filter(Q(domain=site_id) & Q(property=property_id) & Q(is_canceled=0) & Q(bid_type__in=[2, 3]))
            # if register_user is not None:
            #     bid = bid.filter(user=register_user)
            #
            # # -----------------Search-------------------
            # if 'search' in data and data['search'] != "":
            #     search = data['search']
            #     if search.isdigit():
            #         # bid = bid.filter(Q(id=search) | Q(user__phone_no__icontains=search) | Q(bid_amount__icontains=search))
            #         bid = bid.filter(Q(id=search) | Q(registration__bid_registration_address_registration__phone_no__icontains=search) | Q(bid_amount__icontains=search))
            #     else:
            #         # bid = bid.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(user__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
            #         bid = bid.annotate(full_name=Concat('registration__bid_registration_address_registration__first_name', V(' '), 'registration__bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(registration__bid_registration_address_registration__first_name__icontains=search) | Q(registration__bid_registration_address_registration__last_name__icontains=search) | Q(registration__bid_registration_address_registration__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
            # bid = bid.distinct("id")
            # total = bid.count()
            # bid = bid.order_by("-id").only("id")[offset:limit]
            # serializer = SubdomainBidHistorySerializer(bid, many=True)

            new_bid = Bid.objects.values("user").annotate(bids=Count("user")).annotate(start_bid=Min("bid_amount")).annotate(max_bid=Max("bid_amount")).annotate(bid_time=Max("bid_date")).annotate(id=Max("id")).filter(Q(property=property_id) & Q(is_canceled=0))
            if register_user is not None:
                new_bid = new_bid.filter(user=register_user)

            total = new_bid.count()
            new_bid = new_bid.order_by("-bid_time")[offset:limit]
            new_serializer = NewSubdomainBidHistorySerializer(new_bid, many=True, context=property_id)

            property_listing = PropertyListing.objects.get(Q(id=property_id) & Q(domain=site_id))
            property_detail = BidPropertyDetailSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                # 'data': serializer.data,
                'new_data': new_serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
            

class SuperAdminBidHistoryView(APIView):
    """
    Super Admin bid history
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

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            register_user = None
            if "register_user" in data and data['register_user'] != "":
                register_user = int(data['register_user'])

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & Q(user_type=3)).first()
                if not user:
                    return Response(response.parsejson("You are not authorize to access data.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid = Bid.objects.filter(Q(property=property_id) & Q(is_canceled=0) & Q(bid_type__in=[2, 3]))
            if register_user is not None:
                bid = bid.filter(user=register_user)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    bid = bid.filter(Q(id=search) | Q(user__phone_no__icontains=search) | Q(bid_amount__icontains=search))
                else:
                    bid = bid\
                        .annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name'))\
                        .filter(
                            Q(full_name__icontains=search) |
                            Q(user__first_name__icontains=search) |
                            Q(user__last_name__icontains=search) |
                            Q(user__email__icontains=search) |
                            Q(bid_amount__icontains=search) |
                            Q(ip_address__icontains=search)
                        )

            total = bid.count()
            bid = bid.order_by("-id").only("id")[offset:limit]
            serializer = SubdomainBidHistorySerializer(bid, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidHistoryView(APIView):
    """
    Bid history
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            bid = Bid.objects.raw('SELECT max(id) as id, user_id, max(bid_amount) as high_bids, count(id) as bids, max(bid_date) as bid_date FROM bid WHERE property_id ='+str(property_id)+' and domain_id='+str(domain_id)+' and is_canceled=false GROUP BY user_id order by high_bids desc')
            serializer = BidHistorySerializer(bid, many=True, context=property_id)
            all_data = {
                'data': serializer.data,
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionBiddersView(APIView):
    """
    Auction Bidders
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

            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("site_id is required", "", status=403))
                else:
                    site_id = None

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                if is_super_admin is None:
                    user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                    if user is None:
                        return Response(response.parsejson("You are not active user.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.filter(Q(property=property_id) & Q(status=1))
            if site_id is not None:
                bid_registration = bid_registration.filter(Q(domain=site_id))
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = AuctionRegisterSerializer(bid_registration, many=True)

            property_listing = PropertyListing.objects.filter(Q(id=property_id))
            if site_id is not None:
                property_listing = property_listing.filter(Q(domain=site_id))
            property_listing = property_listing.first()
            property_detail = AuctionBiddersSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionTotalBidsView(APIView):
    """
    Auction total bids
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
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("site_id is required", "", status=403))
                else:
                    site_id = None

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                if is_super_admin is None:
                    user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                    if user is None:
                        return Response(response.parsejson("You are not active user.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid = Bid.objects.values("user").annotate(bids=Count("user")).annotate(start_bid=Min("bid_amount")).annotate(max_bid=Max("bid_amount")).annotate(bid_time=Max("bid_date")).annotate(id=Max("id")).filter(Q(property=property_id) & Q(is_canceled=0))
            if site_id is not None:
                bid = bid.filter(Q(domain=site_id))
            total = bid.count()
            bid = bid.order_by("-bid_time")[offset:limit]
            serializer = AuctionTotalBidsSerializer(bid, many=True, context=property_id)

            property_listing = PropertyListing.objects.filter(Q(id=property_id))
            if site_id is not None:
                property_listing = property_listing.filter(Q(domain=site_id))
            property_listing = property_listing.first()
            property_detail = AuctionBiddersSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                # 'data': bid,
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionTotalWatchingView(APIView):
    """
    Auction total watching
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
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("site_id is required", "", status=403))
                else:
                    site_id = None

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                if is_super_admin is None:
                    user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                    if user is None:
                        return Response(response.parsejson("You are not active user.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            watching = PropertyWatcher.objects
            no_anonymous_watcher = watching.filter(Q(property=property_id) & Q(user__isnull=True)).count()
            watching = watching.filter(Q(property=property_id) & Q(user__isnull=False))
            total = watching.count()
            total_watcher = PropertyWatcher.objects.filter(Q(property=property_id)).count()
            watching = watching.order_by("-id")[offset:limit]
            serializer = AuctionTotalWatchingSerializer(watching, many=True)

            property_listing = PropertyListing.objects.filter(Q(id=property_id))
            if site_id is not None:
                property_listing = property_listing.filter(Q(domain=site_id))
            property_listing = property_listing.first()
            property_detail = AuctionBiddersSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                'data': serializer.data,
                "total": total,
                "no_anonymous_watcher": no_anonymous_watcher,
                "total_watcher": total_watcher
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerOfferDetailView(APIView):
    """
    Buyer offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(Q(user=user_id) & Q(master_offer__property=property_id) & Q(master_offer__user=user_id) & Q(master_offer__domain=domain_id) & Q(status=1)).last()
            serializer = BuyerOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestCounterBuyerOfferDetailView(APIView):
    """
    Best counter buyer offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(master_offer__property=property_id) & Q(master_offer__user=user_id) & Q(master_offer__domain=domain_id) & Q(offer_by=2) & Q(status=1)).last()
            if negotiated_offers is not None:
                serializer = BestCounterBuyerOfferDetailSerializer(negotiated_offers)
            else:
                negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(user=user_id) & Q(master_offer__property=property_id) & Q(master_offer__user=user_id) & Q(master_offer__domain=domain_id) & Q(status=1)).last()
                serializer = ExtraBestCounterBuyerOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestCounterSellerOfferDetailView(APIView):
    """
    Best counter seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(master_offer=negotiation_id) & Q(master_offer__domain=domain_id) & Q(offer_by=1) & Q(status=1)).last()
            serializer = BestCounterSellerOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerOfferListingView(APIView):
    """
    Seller offer listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(Q(property=property_id) & Q(domain=domain_id))
            master_offer = master_offer.order_by("-id").only("id")
            serializer = SellerOfferListingSerializer(master_offer, many=True)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerOfferDetailView(APIView):
    """
    Seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "negotiated_id" in data and data['negotiated_id'] != "":
                negotiated_id = int(data['negotiated_id'])
            else:
                return Response(response.parsejson("negotiated_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            offers = MasterOffer.objects.filter(id=negotiated_id).last()
            if offers.property.sale_by_type_id == 4:
                offers = NegotiatedOffers.objects.filter(master_offer__id=negotiated_id).last()
                serializer = SellerOfferDetailSerializer(offers)
            else:
                serializer = SellerOfferDetailsSerializer(offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckAgentView(APIView):
    """
    Check agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not agent.", "", status=403))
                return Response(response.parsejson("Agent is true.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerMakeOfferView(APIView):
    """
    Buyer make offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[4, 7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            # if int(sale_by_type) == 7:  # ----Best and final offer
            #     property_auction = PropertyAuction.objects.filter(property=property_id, status=1).first()
            #     if property_auction is None:
            #         return Response(response.parsejson("Offer not exist.", "", status=403))

            if "offer_price" in data and data['offer_price'] != "":
                offer_price = data['offer_price']
            else:
                return Response(response.parsejson("offer_price is required", "", status=403))

            comment = None
            if "comment" in data and data['comment'] != "":
                comment = data['comment']

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiation_id = None
            check_negotiation_id = None
            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
                check_negotiation_id = int(data['negotiation_id'])

            document_id = None
            if "document_id" in data and type(data['document_id']) == list and len(data['document_id']) > 0:
                document_id = data['document_id']

            if negotiation_id is None:
                if "first_name" in data and data['first_name'] != "":
                    first_name = data['first_name']
                else:
                    return Response(response.parsejson("first_name is required", "", status=403))

                if "last_name" in data and data['last_name'] != "":
                    last_name = data['last_name']
                else:
                    return Response(response.parsejson("last_name is required", "", status=403))

                if "email" in data and data['email'] != "":
                    email = data['email']
                else:
                    return Response(response.parsejson("email is required", "", status=403))

                if "address_first" in data and data['address_first'] != "":
                    address_first = data['address_first']
                else:
                    return Response(response.parsejson("address_first is required", "", status=403))

                if "city" in data and data['city'] != "":
                    city = data['city']
                else:
                    return Response(response.parsejson("city is required", "", status=403))

                if "state" in data and data['state'] != "":
                    state = int(data['state'])
                else:
                    return Response(response.parsejson("state is required", "", status=403))

                if "country" in data and data['country'] != "":
                    country = int(data['country'])
                else:
                    country = None

                if "phone_no" in data and data['phone_no'] != "":
                    phone_no = data['phone_no']
                else:
                    return Response(response.parsejson("phone_no is required", "", status=403))

                if "postal_code" in data and data['postal_code'] != "":
                    postal_code = data['postal_code']
                else:
                    return Response(response.parsejson("postal_code is required", "", status=403))

                if "user_type" in data and data['user_type'] != "":
                    user_type = int(data['user_type'])
                else:
                    return Response(response.parsejson("user_type is required", "", status=403))

                if user_type == 2:
                    if "working_with_agent" in data and data['working_with_agent'] != "":
                        working_with_agent = int(data['working_with_agent'])
                    else:
                        return Response(response.parsejson("working_with_agent is required", "", status=403))
                else:
                    working_with_agent = None
                if (user_type == 2 and not working_with_agent) or (user_type == 4):
                    if "property_in_person" in data and data['property_in_person'] != "":
                        property_in_person = int(data['property_in_person'])
                    else:
                        return Response(response.parsejson("property_in_person is required", "", status=403))

                    if "pre_qualified_lender" in data and data['pre_qualified_lender'] != "":
                        pre_qualified_lender = int(data['pre_qualified_lender'])
                    else:
                        return Response(response.parsejson("pre_qualified_lender is required", "", status=403))
            if negotiation_id is not None:
                master_offer = MasterOffer.objects.filter(id=negotiation_id, domain=domain_id, user=user_id).last()
            elif negotiation_id is None:
                master_offer = MasterOffer.objects.filter(property=property_id, domain=domain_id, user=user_id).last()
            with transaction.atomic():
                try:
                    if master_offer is None:
                        master_offer = MasterOffer()
                        master_offer.domain_id = domain_id
                        master_offer.property_id = property_id
                        master_offer.user_id = user_id
                        master_offer.user_type = user_type
                        master_offer.working_with_agent = working_with_agent
                        master_offer.property_in_person = property_in_person
                        master_offer.pre_qualified_lender = pre_qualified_lender
                        # master_offer.document_id = document_id
                        master_offer.status_id = 1
                        master_offer.save()
                        negotiation_id = master_offer.id

                        offer_address = OfferAddress()
                        offer_address.domain_id = domain_id
                        offer_address.master_offer_id = negotiation_id
                        offer_address.first_name = first_name
                        offer_address.last_name = last_name
                        offer_address.email = email
                        offer_address.address_first = address_first
                        offer_address.city = city
                        offer_address.state_id = state
                        offer_address.country_id = country
                        offer_address.phone_no = phone_no
                        offer_address.postal_code = postal_code
                        offer_address.user_id = user_id
                        offer_address.status_id = 1
                        offer_address.save()

                    # elif master_offer.is_canceled == 1 or master_offer.is_declined == 1 or master_offer.status_id != 1:
                    elif negotiation_id is None:
                        negotiation_id = master_offer.id
                        master_offer.is_canceled = 0
                        master_offer.is_declined = 0
                        master_offer.status_id = 1
                        master_offer.declined_by_id = None
                        master_offer.final_by = None
                        master_offer.user_type = user_type
                        master_offer.working_with_agent = working_with_agent
                        master_offer.property_in_person = property_in_person
                        master_offer.pre_qualified_lender = pre_qualified_lender
                        # master_offer.document_id = document_id
                        master_offer.save()

                        offer_address = OfferAddress.objects.filter(master_offer=negotiation_id).first()
                        if offer_address is None:
                            offer_address = OfferAddress()
                        offer_address.domain_id = domain_id
                        offer_address.master_offer_id = negotiation_id
                        offer_address.first_name = first_name
                        offer_address.last_name = last_name
                        offer_address.email = email
                        offer_address.address_first = address_first
                        offer_address.city = city
                        offer_address.state_id = state
                        offer_address.country_id = country
                        offer_address.phone_no = phone_no
                        offer_address.postal_code = postal_code
                        offer_address.status_id = 1
                        offer_address.user_id = user_id
                        offer_address.save()

                    if document_id is not None and len(document_id) > 0:
                        for document in document_id:
                            offer_documents = OfferDocuments()
                            offer_documents.domain_id = domain_id
                            offer_documents.property_id = property_id
                            offer_documents.master_offer_id = negotiation_id
                            offer_documents.document_id = document
                            offer_documents.status_id = 1
                            offer_documents.save()

                    negotiated_offers = NegotiatedOffers()
                    negotiated_offers.domain_id = domain_id
                    negotiated_offers.property_id = property_id
                    negotiated_offers.master_offer_id = negotiation_id
                    negotiated_offers.user_id = user_id
                    negotiated_offers.offer_by = 1
                    negotiated_offers.display_status = 1
                    negotiated_offers.offer_price = offer_price
                    negotiated_offers.comments = comment
                    negotiated_offers.status_id = 1
                    negotiated_offers.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))
            # ----------------Notifications-----------
            prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
            property_detail = PropertyListing.objects.get(id=property_id)
            agent_detail = Users.objects.get(id=property_detail.agent_id)
            broker_detail = Users.objects.get(site_id=domain_id)
            broker_name = broker_detail.first_name
            broker_email = broker_detail.email
            broker_phone = broker_detail.phone_no
            agent_email = agent_detail.email
            agent_name = agent_detail.first_name
            agent_phone = agent_detail.phone_no

            if check_negotiation_id is None:
                title = "Make an offer"
                content = "You Made an Offer <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                if user_id != agent_id:
                    title = "Make an offer"
                    content = "You Received an Offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                if user_id != broker_detail.id and broker_detail.id != agent_id:
                    title = "Make an offer"
                    content = "New offer was made on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            else:
                title = "Counter offer"
                content = "You Made a Counter-Offer <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                if user_id != agent_id:
                    title = "Counter offer"
                    content = "A Buyer Sent you a Counter-Offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                if user_id != broker_detail.id and broker_detail.id != agent_id:
                    title = "Counter offer"
                    content = "New Counter-Offer was made on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            # ----------Email Send------------------------
            offer_price = data['offer_price']
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            web_url = settings.FRONT_BASE_URL
            image_url = web_url+'/static/admin/images/property-default-img.png'
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            if upload is not None:
                image = upload.upload.doc_file_name
                bucket_name = upload.upload.bucket_name
                image_url = settings.AWS_URL+bucket_name+'/'+image
            property_address = property_detail.address_one
            property_city = property_detail.city
            property_state = property_detail.state.state_name
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            if int(sale_by_type) == 7:
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
            else:
                domain_url = subdomain_url.replace("###", domain_name)+"my-offers"
            buyer_detail = Users.objects.get(id=user_id)
            buyer_name = buyer_detail.first_name
            buyer_email = buyer_detail.email
            buyer_phone = buyer_detail.phone_no
            if check_negotiation_id is None:
                #================Email send buyer==========================
                '''if buyer_email.lower() == agent_email.lower():
                    template_data = {"domain_id": domain_id, "slug": "make_an_offer"}
                    extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'agent_email': agent_email, "domain_id": domain_id}
                else:'''
                template_data = {"domain_id": domain_id, "slug": "make_an_offer_buyer"}
                extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'agent_email': agent_email, "domain_id": domain_id}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                #================Email send property agent======================
                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                
                if buyer_email != agent_email:
                    template_data = {"domain_id": domain_id, "slug": "make_an_offer_agent"}
                    extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'buyer_name': buyer_name.title(), 'buyer_email': buyer_email, 'message': comment, "domain_id": domain_id}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    template_data = {"domain_id": domain_id, "slug": "make_an_offer_agent"}
                    extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'buyer_name': buyer_name.title(), 'buyer_email': buyer_email, 'message': comment, "domain_id": domain_id}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            else:
                #================Send mail Make Counter Offer=====================
                #================Email send buyer==========================
                if buyer_email.lower() == agent_email.lower():
                    template_data = {"domain_id": domain_id, "slug": "counter_offer"}
                    counter_by = 'buyer' 
                    extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'counter_by': counter_by, 'message': comment, "domain_id": domain_id, 'name': agent_name, 'email': agent_email, 'phone': phone_format(agent_phone)}
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                else:
                    counter_by = 'buyer' 
                    template_data = {"domain_id": domain_id, "slug": "counter_offer"}
                    extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'counter_by': counter_by, 'message': comment, "domain_id": domain_id, 'name': agent_name, 'email': agent_email, 'phone': phone_format(agent_phone)}
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                    #================Email send property agent======================
                    template_data = {"domain_id": domain_id, "slug": "make_counter_offer"}
                    if int(sale_by_type) == 7:
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                    else:
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                    
                    extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'message': comment, 'counter_by': counter_by, "domain_id": domain_id, 'name': buyer_name, 'email': buyer_email, 'phone': phone_format(buyer_phone)}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    template_data = {"domain_id": domain_id, "slug": "make_counter_offer"}
                    extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'offer_price': number_format(offer_price), 'message': comment, 'counter_by': counter_by, "domain_id": domain_id, 'name': buyer_name, 'email': buyer_email, 'phone': phone_format(buyer_phone)}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Offer successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerCounterOfferView(APIView):
    """
    Seller counter offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "offer_price" in data and data['offer_price'] != "":
                offer_price = data['offer_price']
            else:
                return Response(response.parsejson("offer_price is required", "", status=403))

            comment = None
            if "comment" in data and data['comment'] != "":
                comment = data['comment']

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for counter.", "", status=403))
            # elif negotiated_offers.offer_by == 2:
            #     return Response(response.parsejson("You can't make two consecutive counter.", "", status=403))

            negotiated_offers = NegotiatedOffers()
            negotiated_offers.domain_id = domain_id
            negotiated_offers.property_id = property_id
            negotiated_offers.master_offer_id = master_id
            negotiated_offers.user_id = user_id
            negotiated_offers.offer_by = 2
            negotiated_offers.display_status = 2
            negotiated_offers.offer_price = offer_price
            negotiated_offers.comments = comment
            negotiated_offers.status_id = 1
            negotiated_offers.save()

            try:
                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                buyer_datail = Users.objects.get(email=master_offer.user)
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                buyer_phone = buyer_datail.phone_no
                user_counter_data = user
                user_counter_name = user_counter_data.first_name if user_counter_data is not None else ""
                user_counter_email = user_counter_data.email if user_counter_data.email is not None else ""
                user_counter_phone = user_counter_data.phone_no if user_counter_data.phone_no is not None else ""
                if user_counter_data.site_id and user_counter_data.site_id == domain_id: #counter by broker
                    counter_by = 'seller'
                    other_user_detail = Users.objects.get(id=property_listing.agent_id)
                else: # counter by agent
                    counter_by = 'seller'
                    other_user_detail = Users.objects.get(site_id=domain_id)
                other_user_name = other_user_detail.first_name if other_user_detail.first_name is not None else ""
                other_user_email = other_user_detail.email if other_user_detail.email is not None else ""

                title = "Counter Offer"
                content = "You made a Counter-Offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                # to other agent/broker
                if user_id != other_user_detail.id:
                    title = "Counter Offer"
                    content = "New counter offer made by "+ counter_by +" on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=other_user_detail.id, added_by=user_id, notification_for=1, property_id=property_id)

                # notification to buyer
                if user_id != master_offer.user_id:
                    content = "You’ve Received a Counter-Offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=master_offer.user_id, added_by=user_id, notification_for=1, property_id=property_id)

                
                #==================Email send=============================
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_listing.address_one
                property_city = property_listing.city
                property_state = property_listing.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name

                #================Email send buyer/broker/agent==========================
                template_data = {"domain_id": domain_id, "slug": "counter_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {
                    "user_name": user_counter_name,
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    'offer_price': number_format(offer_price),
                    'message': comment,
                    'counter_by': counter_by,
                    "domain_id": domain_id,
                    'name': buyer_name,
                    'email': buyer_email,
                    'phone': phone_format(buyer_phone)
                }
                compose_email(to_email=[user_counter_email], template_data=template_data, extra_data=extra_data) 

                if negotiated_offers.user.id != other_user_detail.id:
                    extra_data['user_name'] = other_user_name
                    compose_email(to_email=[other_user_email], template_data=template_data, extra_data=extra_data)
                

                if negotiated_offers.user.id != master_offer.user.id:
                    template_data = {"domain_id": domain_id, "slug": "make_counter_offer"}
                    domain_url = subdomain_url.replace("###", domain_name)+"my-offers"
                    extra_data = {
                        "user_name": buyer_name.title(),
                        'web_url': web_url,
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'property_image': image_url,
                        'dashboard_link': domain_url,
                        'offer_price': number_format(offer_price),
                        'counter_by': counter_by,
                        'message': comment,
                        "domain_id": domain_id,
                        'name': user_counter_name,
                        'email': user_counter_email,
                        'phone': phone_format(user_counter_phone)
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)     
            except:
                pass   

            return Response(response.parsejson("Counter offer successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerAcceptOfferView(APIView):
    """
    Buyer accept offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[4, 7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 1:
                return Response(response.parsejson("You can't accept offer.", "", status=403))

            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 1
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()
            # ----------------Notifications-----------
            prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
            title = "Offer accepted"
            content = "You accepted an offer! <span>[" + prop_name + "]</span>"
            add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

            title = "Offer accepted"
            content = "Buyer accepted your offer! <span>[" + prop_name + "]</span>"
            add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            title = "Property sold"
            content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
            add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            # ===========Send Email===========================
            property_detail = PropertyListing.objects.get(id=property_id)
            broker_detail = Users.objects.get(site_id=domain_id)
            broker_name = broker_detail.first_name
            broker_email = broker_detail.email
            buyer_datail = Users.objects.get(id=user_id)
            buyer_name = buyer_datail.first_name
            buyer_email = buyer_datail.email
            buyer_phone = buyer_datail.phone_no
            agent_detail = Users.objects.get(id=property_detail.agent_id)
            agent_email = agent_detail.email
            agent_name = agent_detail.first_name
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            web_url = settings.FRONT_BASE_URL
            image_url = web_url+'/static/admin/images/property-default-img.png'
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            if upload is not None:
                image = upload.upload.doc_file_name
                bucket_name = upload.upload.bucket_name
                image_url = settings.AWS_URL+bucket_name+'/'+image
            property_address = property_detail.address_one
            property_city = property_detail.city
            property_state = property_detail.state.state_name
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            if int(sale_by_type) == 7:
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
            else:
                domain_url = subdomain_url.replace("###", domain_name)+"my-offers"
            template_data = {"domain_id": domain_id, "slug": "accept_offer"}
            #================Email send buyer==========================
            if agent_email.lower() == buyer_email.lower():
                accepted_by = 'buyer' 
                extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            else:
                accepted_by = 'buyer' 
                extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                #================Email send property agent======================
                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #================Email send broker agent======================
            if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerAcceptOfferView(APIView):
    """
    Seller accept offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id
            master_user_id = master_offer.user_id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 2:
                return Response(response.parsejson("You can't accept offer.", "", status=403))

            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 2
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()

            # ----------------Notifications-----------
            prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
            property_detail = property_listing
            broker_detail = Users.objects.get(site_id=domain_id)
            broker_name = broker_detail.first_name
            broker_email = broker_detail.email
            buyer_datail = master_offer.user
            buyer_name = buyer_datail.first_name
            buyer_email = buyer_datail.email
            agent_detail = property_detail.agent
            agent_email = agent_detail.email
            agent_name = agent_detail.first_name
            accept_email = user.email if user.email is not None else ""
            accept_name = user.first_name if user.first_name is not None else ""
            accept_phone = user.phone_no if user.phone_no is not None else "" 
            
            # notif to buyer
            if user_id != master_user_id:
                title = "Offer accepted"
                content = "Seller has accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=master_user_id, added_by=user_id, notification_for=1, property_id=property_id)

            #  notif to agent/broker for accept
            title = "Offer accepted."
            content = "You accepted an offer! <span>[" + prop_name + "]</span>"
            add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            content = "An offer was accepted by seller on! <span>[" + prop_name + "]</span>"
            if user_id != broker_detail.id:
                add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)
            if user_id != agent_detail.id:
                add_notification(domain_id, title, content, user_id=agent_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

            # sold notif to agent and broker
            title = "Property Sold"
            content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
            add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)
            
            if agent_id != broker_detail.id:
                content = "A Property has been Sold! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)




            #===========Send Email===========================
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            web_url = settings.FRONT_BASE_URL
            image_url = web_url+'/static/admin/images/property-default-img.png'
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            if upload is not None:
                image = upload.upload.doc_file_name
                bucket_name = upload.upload.bucket_name
                image_url = settings.AWS_URL+bucket_name+'/'+image
            property_address = property_detail.address_one
            property_city = property_detail.city
            property_state = property_detail.state.state_name
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            if int(sale_by_type) == 7:
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
            else:
                domain_url = subdomain_url.replace("###", domain_name)+"my-offers"
            template_data = {"domain_id": domain_id, "slug": "accept_offer"}
            #================Email send buyer==========================
            if buyer_email.lower() == agent_email.lower():
                accepted_by = 'seller' 
                extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            else:
                accepted_by = 'seller' 
                extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                #================Email send property agent======================
                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #================Email send broker agent======================
            if agent_email.lower() != broker_email.lower() and agent_email.lower() != buyer_email.lower():
                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class OfferDetailView(APIView):
    """
    Offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(domain=domain_id)).first()
            if property_listing is None:
                return Response(response.parsejson("Property not exist.", "", status=403))
            elif property_listing is not None and property_listing.sale_by_type_id != 4:
                return Response(response.parsejson("Property is not traditional direct offer.", "", status=403))
            else:
                property_auction = PropertyAuction.objects.filter(property=property_id).first()
            users = Users.objects.get(Q(id=user_id) & Q(status=1))
            serializer = OfferDetailSerializer(users)
            all_data = {
                'user_detail': serializer.data,
                'asking_price': property_auction.start_price,
                'due_diligence_period': property_listing.due_diligence_period,
                'escrow_period': property_listing.escrow_period,
                'earnest_deposit': property_listing.earnest_deposit
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MyOfferListingView(APIView):
    """
    My offer listing
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
                
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            property_listing = PropertyListing.objects.filter(Q(sale_by_type=4) & Q(domain=domain_id) & Q(master_offer_property__user=user_id))
            total = property_listing.count()
            # property_listing = property_listing.order_by("-id").only("id")[offset: limit]
            property_listing = property_listing.order_by("-master_offer_property__id").only("id")[offset: limit]
            serializer = MyOfferListingSerializer(property_listing, many=True, context=user_id)
            all_data = {
                'data': serializer.data,
                'total': total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestOfferListingView(APIView):
    """
    Best offer listing
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

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            property_listing = PropertyListing.objects.filter(Q(sale_by_type=7) & Q(domain=domain_id) & Q(master_offer_property__user=user_id)).exclude(status=5)
            total = property_listing.count()
            # property_listing = property_listing.order_by("-id").only("id")[offset: limit]
            property_listing = property_listing.order_by("-master_offer_property__id").only("id")[offset: limit]
            serializer = BestOfferListingSerializer(property_listing, many=True, context=user_id)
            all_data = {
                'data': serializer.data,
                'total': total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestOfferListingView(APIView):
    """
    Enhanced Best offer listing
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

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            property_listing = PropertyListing.objects.filter(Q(sale_by_type=7) & Q(domain=domain_id) & Q(master_offer_property__user=user_id)).exclude(status=5)
            total = property_listing.count()
            # property_listing = property_listing.order_by("-id").only("id")[offset: limit]
            property_listing = property_listing.order_by("-master_offer_property__id").only("id")[offset: limit]
            serializer = EnhancedBestOfferListingSerializer(property_listing, many=True, context=user_id)
            all_data = {
                'data': serializer.data,
                'total': total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerRejectOfferView(APIView):
    """
    Buyer reject offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            declined_reason = None
            if "declined_reason" in data and data['declined_reason'] != "":
                declined_reason = data['declined_reason']

            master_offer = MasterOffer.objects.filter(property=property_id, user=user_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("You can't reject offer.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            address_one = master_offer.property.address_one
            agent_id = master_offer.property.agent_id
            master_offer.is_declined = 1
            master_offer.declined_by_id = user_id
            master_offer.final_by = 1
            master_offer.declined_reason = declined_reason
            master_offer.save()

            try:
                #===========Send Email===========================
                property_detail = master_offer.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                agent_detail = master_offer.property.agent
                agent_email = agent_detail.email
                agent_name = agent_detail.first_name

                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                    
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                sale_by_type = property_detail.sale_by_type_id
                rejected_name = buyer_name.title()
                rejected_email = buyer_email
                rejected_phone = phone_format(buyer_datail.phone_no)

                if int(sale_by_type) == 7:
                    domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                    admin_domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest offer"
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"my-offers"
                    admin_domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional offer"
                
                # ----------------Notifications-----------
                prop_name = master_offer.property.address_one if master_offer.property.address_one else master_offer.property.id
                title = "Offer rejected" if property_detail.sale_by_type_id != 7 else "Highest & Best offer rejected"
                content = "You have rejected an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)
                
                if user_id != agent_id:
                    title = "Offer rejected" if property_detail.sale_by_type_id != 7 else "Highest & Best offer rejected"
                    content = "Your Offer was rejected by buyer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)


                if int(sale_by_type) == 7:
                    # send email to buyer
                    template_data = {"domain_id": domain_id, "slug": "loi_was_declined"}
                    negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
                    loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                    extra_data = {
                        "user_name": buyer_name.title(),
                        'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'declined_by': 'buyer',
                        'decline_reason':master_offer.declined_reason if master_offer.declined_reason else 'NA',
                        "domain_id": domain_id,
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "domain_name":domain_name,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[master_offer.user.email], template_data=template_data, extra_data=extra_data)
                else: #other than highest and best offer
                    template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                    extra_data = {
                        'web_url': web_url,
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'property_image': image_url,
                        'dashboard_link': domain_url,
                        "domain_id": domain_id,
                        'rejected_name': rejected_name,
                        'rejected_email': rejected_email,
                        'rejected_phone': rejected_phone,
                        'content_message': 'You have rejected an offer',
                        'user_name': buyer_name.title()
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    "domain_id": domain_id,
                    'rejected_name': rejected_name,
                    'rejected_email': rejected_email,
                    'rejected_phone': rejected_phone,
                }
                if property_detail.sale_by_type_id == 7:
                    extra_data['subject'] = 'Highest and Best Offer has been rejected'
                if buyer_email.lower() != agent_email.lower():
                    #================Email send property agent======================
                    extra_data['content_message'] = 'Your Offer has been Rejected By Buyer'
                    extra_data['user_name'] =  agent_name
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    #================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    extra_data['content_message'] = 'Your Offer has been Rejected By Buyer'
                    extra_data['user_name'] =  broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer rejected successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBuyerRejectOfferView(APIView):
    """
    Buyer reject offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (
                            Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            declined_reason = None
            if "declined_reason" in data and data['declined_reason'] != "":
                declined_reason = data['declined_reason']

            master_offer = MasterOffer.objects.filter(property=property_id, user=user_id, status=1, is_canceled=0,
                                                      is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("You can't reject offer.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            highest_best_negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id).last()
            highest_best_negotiated_offers.display_status = 4
            highest_best_negotiated_offers.declined_reason = declined_reason
            highest_best_negotiated_offers.is_declined = 1
            highest_best_negotiated_offers.save()
            address_one = master_offer.property.address_one
            agent_id = master_offer.property.agent_id
            master_offer.is_declined = 1
            master_offer.declined_by_id = user_id
            master_offer.final_by = 1
            master_offer.declined_reason = declined_reason
            master_offer.save()

            try:
                # ===========Send Email===========================
                property_detail = master_offer.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                agent_detail = master_offer.property.agent
                agent_email = agent_detail.email
                agent_name = agent_detail.first_name

                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url + '/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL + bucket_name + '/' + image

                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                sale_by_type = property_detail.sale_by_type_id
                rejected_name = buyer_name.title()
                rejected_email = buyer_email
                rejected_phone = phone_format(buyer_datail.phone_no)

                domain_url = subdomain_url.replace("###", domain_name) + "best-offers"
                admin_domain_url = subdomain_url.replace("###",
                                                             domain_name) + "admin/listing/?auction_type=highest%20offer"

                # ----------------Notifications-----------
                prop_name = master_offer.property.address_one if master_offer.property.address_one else master_offer.property.id
                title = "Highest & Best offer rejected"
                content = "You have rejected an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1,
                                property_id=property_id, notification_type=1)

                if user_id != agent_id:
                    content = "Your Offer was rejected by buyer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)
                
                if agent_id != broker_detail.id:
                    content = "An Offer was rejected by buyer on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)

                if int(sale_by_type) == 7:
                    # send email to buyer
                    template_data = {"domain_id": domain_id, "slug": "loi_was_declined"}
                    negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
                    loi_url = subdomain_url.replace("###", domain_name) + "submit-loi/?property_id=" + str(property_id)
                    extra_data = {
                        "user_name": buyer_name.title(),
                        'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'declined_by': 'buyer',
                        'decline_reason': master_offer.declined_reason if master_offer.declined_reason else 'NA',
                        "domain_id": domain_id,
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "domain_name": domain_name,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[master_offer.user.email], template_data=template_data,
                                  extra_data=extra_data)
                else:  # other than highest and best offer
                    template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                    extra_data = {
                        'web_url': web_url,
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'property_image': image_url,
                        'dashboard_link': domain_url,
                        "domain_id": domain_id,
                        'rejected_name': rejected_name,
                        'rejected_email': rejected_email,
                        'rejected_phone': rejected_phone,
                        'content_message': 'You have rejected an offer',
                        'user_name': buyer_name.title()
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': admin_domain_url,
                    "domain_id": domain_id,
                    'rejected_name': rejected_name,
                    'rejected_email': rejected_email,
                    'rejected_phone': rejected_phone,
                }
                if property_detail.sale_by_type_id == 7:
                    extra_data['subject'] = 'Highest and Best Offer has been rejected'
                if buyer_email.lower() != agent_email.lower():
                    # ================Email send property agent======================
                    extra_data['content_message'] = 'Your Offer has been Rejected By Buyer'
                    extra_data['user_name'] = agent_name
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    # ================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    extra_data['content_message'] = 'Your Offer has been Rejected By Buyer'
                    extra_data['user_name'] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer rejected successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerRejectOfferView(APIView):
    """
    Seller reject offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            declined_reason = None
            if "declined_reason" in data and data['declined_reason'] != "":
                declined_reason = data['declined_reason']

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("You can't reject offer.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            property_id = master_offer.property_id
            address_one = master_offer.property.address_one
            buyer_id = master_offer.user_id
            master_offer.is_declined = 1
            master_offer.declined_by_id = user_id
            master_offer.final_by = 2
            master_offer.declined_reason = declined_reason
            master_offer.save()

            try:
                # ===========Send Email===========================
                property_detail = master_offer.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone =  broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                agent_detail = master_offer.property.agent
                agent_email = agent_detail.email
                agent_name = agent_detail.first_name

                upload = PropertyUploads.objects.filter(property=master_offer.property.id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=master_offer.property.id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image

                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                domain_url = subdomain_url.replace("###", domain_name)+"my-offers"

                rejected_name = user.first_name
                rejected_email = user.email
                rejected_phone = phone_format(user.phone_no)

                # ----------------Notifications-----------
                prop_name = master_offer.property.address_one if master_offer.property.address_one else master_offer.property.id
                title = "Offer rejected"
                content = "You have rejected an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)
                
                #  notif to broker/agent
                content = "An Offer was rejected by seller on! <span>[" + prop_name + "]</span>"
                if user_id != broker_detail.id:
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)
                
                if user_id != agent_detail.id:
                    add_notification(domain_id, title, content, user_id=agent_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                #  notif to buyer
                if user_id != buyer_id:
                    content = "Your Offer was rejected by seller! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=buyer_id, added_by=user_id, notification_for=1, property_id=property_id)

                    template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                    extra_data = {
                        'web_url': web_url,
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'property_image': image_url,
                        'dashboard_link': domain_url,
                        "domain_id": domain_id,
                        'rejected_name': rejected_name,
                        'rejected_email': rejected_email,
                        'rejected_phone': rejected_phone,
                        'user_name': buyer_name.title()
                    }
                    extra_data['content_message'] = 'Your Offer has been Rejected By Seller'
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                
                # send email to broker and agent
                template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    "domain_id": domain_id,
                    'rejected_name': rejected_name,
                    'rejected_email': rejected_email,
                    'rejected_phone': rejected_phone,
                }
                extra_data['content_message'] = 'You have rejected an offer'
                extra_data['user_name'] =  user.first_name
                compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

                extra_data['content_message'] = 'An Offer has been Rejected By Seller'
                if user_id != broker_detail.id:
                    extra_data['user_name'] =  broker_detail.first_name
                    compose_email(to_email=[broker_detail.email], template_data=template_data, extra_data=extra_data)

                if user_id != agent_detail.id:
                    extra_data['user_name'] =  agent_detail.first_name
                    compose_email(to_email=[agent_detail.email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer rejected successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedSellerRejectOfferView(APIView):
    """
    Enhanced Seller reject offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            declined_reason = None
            if "declined_reason" in data and data['declined_reason'] != "":
                declined_reason = data['declined_reason']

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("You can't reject offer.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            # get current highest
            max_offer = HighestBestNegotiatedOffers.objects \
                    .filter(status=1, is_declined=0, property=master_offer.property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                    .order_by('-offer_price').first()

            highest_best_negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id).last()
            highest_best_negotiated_offers.display_status = 4
            highest_best_negotiated_offers.declined_reason = declined_reason
            highest_best_negotiated_offers.is_declined = 1
            highest_best_negotiated_offers.save()
            property_id = master_offer.property_id
            address_one = master_offer.property.address_one
            buyer_id = master_offer.user_id
            master_offer.is_declined = 1
            master_offer.declined_by_id = user_id
            master_offer.final_by = 2
            master_offer.declined_reason = declined_reason
            master_offer.save()

            try:
                # ===========Send Email===========================
                property_detail = master_offer.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone =  broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                upload = PropertyUploads.objects.filter(property=master_offer.property.id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=master_offer.property.id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                rejected_name = user.first_name
                rejected_email = user.email
                rejected_phone = phone_format(user.phone_no)

                #  notifications to broker and agent
                prop_name = master_offer.property.address_one if master_offer.property.address_one else master_offer.property.id
                title = "Highest & Best offer rejected"
                content = "You have rejected an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                content = "An Offer was rejected by seller on! <span>[" + prop_name + "]</span>"
                if user_id != broker_detail.id:
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
                
                if user_id != property_detail.agent.id:
                    add_notification(domain_id, title, content, user_id=property_detail.agent.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                #  notification and email to buyer
                if user_id != buyer_id:
                    content = "Your Offer was rejected by seller! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=buyer_id, added_by=user_id, notification_for=1, property_id=property_id, notification_type=1)

                    template_data = {"domain_id": domain_id, "slug": "loi_was_declined"}
                    declined_by = 'broker' if broker_detail.id == user.id else 'agent'
                    negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_offer.id, status=1).last()
                    loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                    extra_data = {
                        "user_name": buyer_name.title(),
                        'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                        'property_address': property_address,
                        'property_city': property_city,
                        'property_state': property_state,
                        'declined_by': declined_by,
                        'decline_reason': master_offer.declined_reason if master_offer.declined_reason else 'NA',
                        "domain_id": domain_id,
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "domain_name":domain_name,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[master_offer.user.email], template_data=template_data, extra_data=extra_data)


                template_data = {"domain_id": domain_id, "slug": "reject_offer"}
                admin_domain_url = subdomain_url.replace("###",domain_name) + "admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': admin_domain_url,
                    "domain_id": domain_id,
                    'rejected_name': rejected_name,
                    'rejected_email': rejected_email,
                    'rejected_phone': rejected_phone,
                    'subject': 'Highest and Best Offer has been rejected'
                }

                #================Email send property agent/broekr======================
                extra_data['content_message'] = 'You have rejected an offer'
                extra_data['user_name'] =  rejected_name
                compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

                #================Email send broker/agent======================
                extra_data['content_message'] = 'An Offer has been Rejected By Seller'
                if user_id != broker_detail.id:
                    extra_data['user_name'] =  broker_name
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)

                if user_id != property_detail.agent.id:
                    extra_data['user_name'] =  property_detail.agent.first_name
                    compose_email(to_email=[property_detail.agent.email], template_data=template_data, extra_data=extra_data)
                
                # identify new high bidder user
                cur_max_offer = HighestBestNegotiatedOffers.objects \
                    .filter(status=1, is_declined=0, property=property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                    .order_by('-offer_price').first()
                
                if cur_max_offer.id != max_offer:
                    template_data = {"domain_id": domain_id, "slug": "loi_is_the_high_offer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": cur_max_offer.master_offer.user.first_name if cur_max_offer.master_offer.user.first_name is not None else "",
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": cur_max_offer.offer_price,
                        "dashbaord_link": subdomain_url.replace("###",
                                                                domain_name) + 'asset-details/?property_id=' + str(property_id)
                    }
                    compose_email(to_email=[cur_max_offer.master_offer.user.email], template_data=template_data,
                                    extra_data=extra_data)




            except:
                pass

            return Response(response.parsejson("Offer rejected successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminOfferListingView(APIView):
    """
    Admin offer listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            master_offer = MasterOffer.objects.filter(Q(property=property_id))
            master_offer = master_offer.order_by("-id").only("id")
            serializer = AdminOfferListingSerializer(master_offer, many=True)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminOfferDetailView(APIView):
    """
    Seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "negotiated_id" in data and data['negotiated_id'] != "":
                negotiated_id = int(data['negotiated_id'])
            else:
                return Response(response.parsejson("negotiated_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer__id=negotiated_id).last()
            serializer = AdminOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ClearOfferView(APIView):
    """
    Clear offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(Q(property=property_id) & Q(domain=domain_id)).delete()
            master_offer = MasterOffer.objects.filter(Q(property=property_id) & Q(domain=domain_id)).delete()
            return Response(response.parsejson("Deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminClearOfferView(APIView):
    """
    Admin clear offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(Q(property=property_id)).delete()
            master_offer = MasterOffer.objects.filter(Q(property=property_id)).delete()
            return Response(response.parsejson("Deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetOfferDocumentsView(APIView):
    """
    Get offer documents
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[4, 7]).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            documents = OfferDocuments.objects.filter(property=property_id, master_offer=negotiation_id, status=1).order_by("-id").values("id", doc_file_name=F("document__doc_file_name"), bucket_name=F("document__bucket_name"))

            return Response(response.parsejson("Fetch data.", documents, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendBidEmailView(APIView):
    """
    Send bid email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            bid_amount = data['bid_amount'] if data['bid_amount'] is not None else 0

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL+'/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name)+"asset-details/?property_id="+str(property_id)
            
            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            template_data = {"domain_id": domain_id, "slug": "bid_confirmation"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data) 

            extra_data['buyer_name'] = user.first_name + ' ' + user.last_name
            extra_data['buyer_email'] = user.email
            extra_data['buyer_phone'] =phone_format(user.phone_no)
            extra_data['dashboard_link'] = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name)+"admin/listing/"

            if user.id != auction_data.property.agent.id:
                # send email to agent
                extra_data['user_name'] = auction_data.property.agent.first_name.title() + ' ' + auction_data.property.agent.last_name.title()
                template_data = {"domain_id": domain_id, "slug": "bid_confirmation_seller"}
                compose_email(to_email=[auction_data.property.agent.email], template_data=template_data, extra_data=extra_data) 
            if broker_detail.id != auction_data.property.agent.id and user_id != broker_detail.id:
                # send email to broker
                extra_data['user_name'] = broker_detail.first_name.title() + ' ' + broker_detail.last_name.title()
                template_data = {"domain_id": domain_id, "slug": "bid_confirmation_seller"}
                compose_email(to_email=[broker_detail.email], template_data=template_data, extra_data=extra_data)

            prop_name = auction_data.property.address_one if auction_data.property.address_one else auction_data.property.id
            try:
                # send email to outbidder
                outbidder = Bid.objects\
                    .filter(bid_type__in=[2, 3], is_canceled=0, property=property_id)\
                    .exclude(user_id=user_id)\
                    .order_by('-id')\
                    .first()
                # outbidder_id = outbidder[0].user_id
                if outbidder and outbidder.user.id and user_id != outbidder.user.id:
                    extra_data['dashboard_link'] = domain_url
                    extra_data['user_name'] = outbidder.user.first_name.title() + ' ' + outbidder.user.last_name.title()
                    extra_data['bid_amount'] = number_format(outbidder.bid_amount)
                    template_data = {"domain_id": domain_id, "slug": "outbid"}
                    compose_email(to_email=[outbidder.user.email], template_data=template_data, extra_data=extra_data)
                    
                    #  add notfification to buyer(outbidder)
                    content = "You have been outbid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "OutBid Alert",
                        content,
                        user_id=outbidder.user.id,
                        added_by=outbidder.user.id,
                        notification_for=1,
                        property_id=property_id
                    )
            except:
                pass

            try:
                #  add notfification to buyer
                content = "Your bid has been confirmed! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain_id,
                    "Bid Confirmation",
                    content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    property_id=property_id
                )
                if user_id != auction_data.property.agent.id:
                    content = "You have received one new bid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "Bid Received",
                        content,
                        user_id=auction_data.property.agent.id,
                        added_by=auction_data.property.agent.id,
                        notification_for=2,
                        property_id=property_id
                    )
                if broker_detail.id != auction_data.property.agent.id and user_id != broker_detail.id:
                    content = "You have received one new bid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "Bid Received",
                        content,
                        user_id=broker_detail.id,
                        added_by=broker_detail.id,
                        notification_for=2,
                        property_id=property_id
                    )

            except:
                pass

            # message = "Property="+str(property_id)+" Domain id="+str(domain_id)+" User Id="+str(user_id)+" Bid amount="+str(bid_amount)
            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestFinalDetailView(APIView):
    """
    Best and final detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            user = Users.objects.get(id=user_id)
            serializer = BestFinalDetailSerializer(user, context=property_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestFinalDetailView(APIView):
    """
    Enhanced Best and final detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            user = Users.objects.get(id=user_id)
            serializer = EnhancedBestFinalDetailSerializer(user, context=property_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerMakeLoiView(APIView):
    """
    Buyer make LOI
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found1.", "", status=403))
                agent_id = property_listing.agent_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))
            max_dt = timezone.now()
            property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt, end_date__gte=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer not started yet., end date.", "", status=403))
            if property_auction.status_id != 1:
                return Response(response.parsejson("Offer not active.", "", status=403))

            if "offer_price" in data and data['offer_price'] != "":
                offer_price = data['offer_price']
            else:
                return Response(response.parsejson("offer_price is required", "", status=403))

            comment = None
            if "offer_comment" in data and data['offer_comment'] != "":
                comment = data['offer_comment']

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
                check_negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers()
            negotiated_offers.domain_id = domain_id
            negotiated_offers.property_id = property_id
            negotiated_offers.master_offer_id = negotiation_id
            negotiated_offers.user_id = user_id
            negotiated_offers.offer_by = 1
            negotiated_offers.display_status = 1
            negotiated_offers.offer_price = offer_price
            negotiated_offers.comments = comment
            negotiated_offers.status_id = 1
            negotiated_offers.save()
            # ----------------Notifications-----------
            prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
            if check_negotiation_id is None:
                title = "Highest & Best offer"
                content = "You Made Highest and Best Offer <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best offer"
                content = "You Received an Offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
            else:
                title = "Highest & Best Counter offer"
                content = "You Made a Counter-Offer <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best Counter offer"
                content = "A Buyer Sent you a Counter-Offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
            
            try:
                #send email============================
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                broker_email = broker_detail.email if broker_detail.email is not None else ""
                broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                agent_detail = negotiated_offers.property.agent
                agent_email = agent_detail.email if agent_detail.email is not None else ""
                agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                buyer_detail = negotiated_offers.user
                buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                property_address = property_detail.address_one if property_detail.address_one is not None else ""
                property_city = property_detail.city if property_detail.city is not None else ""
                property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                domain_name = network.domain_name
                subdomain_url = settings.SUBDOMAIN_URL
                loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                offer_price = data['offer_price']
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                if check_negotiation_id is None:
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_buyer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": broker_name,
                        "email": broker_email,
                        "phone": phone_format(broker_phone),
                        "loi_link": loi_url
                    }
                    #send to buyer
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                    #send to agent and broker
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_seller"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": broker_name,
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": buyer_name,
                        "email": buyer_email,
                        "phone": phone_format(buyer_phone)
                    }
                    if agent_email.lower() != buyer_email.lower():
                        extra_data['user_name'] = agent_name.title()
                        compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    if broker_email.lower() != agent_email.lower():
                        extra_data['user_name'] = broker_name.title()
                        compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                else:
                    # send email to buyer
                    domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                    template_data = {"domain_id": domain_id, "slug": "counter_offer"}
                    extra_data = {
                        "user_name": buyer_name.title(),
                        "name": agent_name.title(),
                        "email": agent_email,
                        "phone": phone_format(agent_phone),
                        "offer_price": number_format(offer_price),
                        "message": comment,
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "property_image": image_url,
                        "dashboard_link": domain_url  
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send email to agent and broker
                    template_data = {"domain_id": domain_id, "slug": "make_counter_offer"}
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                    extra_data = {
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "property_image": image_url,
                        "dashboard_link": domain_url,
                        "offer_price": number_format(offer_price),
                        "message": comment,
                        "counter_by": 'buyer',
                        "domain_id": domain_id,
                        "name": buyer_name,
                        "email": buyer_email,
                        "phone": phone_format(buyer_phone)
                    }
                    if agent_email.lower() != buyer_email.lower():
                        extra_data['user_name'] = agent_name.title()
                        compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                    if broker_email.lower() != agent_email.lower():
                        extra_data['user_name'] = broker_name.title()
                        compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass
            
            return Response(response.parsejson("LOI successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBuyerMakeLoiView(APIView):
    """
    Enhanced Buyer make LOI
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1,
                                                                  status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))
            max_dt = timezone.now()
            # property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt, end_date__gte=max_dt).first()
            property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer not started yet., end date.", "", status=403))
            if property_auction.status_id != 1:
                return Response(response.parsejson("Offer not active.", "", status=403))

            if "offer_price" in data and data['offer_price'] != "":
                offer_price = data['offer_price']
            else:
                return Response(response.parsejson("offer_price is required", "", status=403))

            comment = None
            if "offer_comment" in data and data['offer_comment'] != "":
                comment = data['offer_comment']

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (
                            Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
                check_negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "earnest_money_deposit" in data and data['earnest_money_deposit'] != "":
                earnest_money_deposit = data['earnest_money_deposit']
            else:
                return Response(response.parsejson("earnest_money_deposit is required", "", status=403))

            if "down_payment" in data and data['down_payment'] != "":
                down_payment = data['down_payment']
            else:
                return Response(response.parsejson("down_payment is required", "", status=403))

            if "due_diligence_period" in data and data['due_diligence_period'] != "":
                due_diligence_period = int(data['due_diligence_period'])
            else:
                return Response(response.parsejson("due_diligence_period is required", "", status=403))

            if "closing_period" in data and data['closing_period'] != "":
                closing_period = int(data['closing_period'])
                if property_listing.escrow_period is not None and closing_period > property_listing.escrow_period:
                    return Response(response.parsejson("closing_period should be less or equal to " + str(property_listing.escrow_period), "", status=403))
            else:
                return Response(response.parsejson("closing_period is required", "", status=403))

            if "financing" in data and data['financing'] != "":
                financing = int(data['financing'])
            else:
                return Response(response.parsejson("financing is required", "", status=403))

            if "offer_contingent" in data and data['offer_contingent'] != "":
                offer_contingent = int(data['offer_contingent'])
            else:
                return Response(response.parsejson("offer_contingent is required", "", status=403))

            if "sale_contingency" in data and data['sale_contingency'] != "":
                sale_contingency = int(data['sale_contingency'])
            else:
                return Response(response.parsejson("sale_contingency is required", "", status=403))

            if "appraisal_contingent" in data and data['appraisal_contingent'] != "":
                appraisal_contingent = int(data['appraisal_contingent'])
            else:
                return Response(response.parsejson("appraisal_contingent is required", "", status=403))

            if "closing_cost" in data and data['closing_cost'] != "":
                closing_cost = int(data['closing_cost'])
            else:
                return Response(response.parsejson("closing_cost is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))

            master_offer_count = MasterOffer.objects.filter(property=property_id, accepted_by__isnull=False).count()
            if master_offer_count:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers()
            negotiated_offers.domain_id = domain_id
            negotiated_offers.property_id = property_id
            negotiated_offers.master_offer_id = negotiation_id
            negotiated_offers.user_id = user_id
            negotiated_offers.offer_by = 1
            negotiated_offers.display_status = 1
            negotiated_offers.offer_price = offer_price
            negotiated_offers.comments = comment
            negotiated_offers.status_id = 1
            negotiated_offers.earnest_money_deposit = earnest_money_deposit
            negotiated_offers.down_payment = down_payment
            negotiated_offers.due_diligence_period = due_diligence_period
            negotiated_offers.closing_period = closing_period
            negotiated_offers.financing = financing
            negotiated_offers.offer_contingent = offer_contingent
            negotiated_offers.sale_contingency = sale_contingency
            negotiated_offers.appraisal_contingent = appraisal_contingent
            negotiated_offers.closing_cost = closing_cost
            negotiated_offers.save()

            try:
                # send email============================
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                broker_email = broker_detail.email if broker_detail.email is not None else ""
                broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                agent_detail = negotiated_offers.property.agent
                agent_email = agent_detail.email if agent_detail.email is not None else ""
                agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                buyer_detail = negotiated_offers.user
                buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                property_address = property_detail.address_one if property_detail.address_one is not None else ""
                property_city = property_detail.city if property_detail.city is not None else ""
                property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                domain_name = network.domain_name
                subdomain_url = settings.SUBDOMAIN_URL
                loi_url = subdomain_url.replace("###", domain_name) + "submit-loi/?property_id=" + str(property_id)
                web_url = settings.FRONT_BASE_URL
                image_url = web_url + '/static/admin/images/property-default-img.png'
                offer_price = data['offer_price']
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL + bucket_name + '/' + image
                closing_period_text = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}

                # ----------------Notifications-----------
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id
                
                title = "Highest & Best Counter offer"
                content = "You Made a Counter-Offer <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1,
                                    property_id=property_id)

                if user_id != agent_id:
                    content = "A Buyer Sent you a Counter-Offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)

                                    
                if broker_email.lower() != agent_email.lower() and user_id != broker_detail.id:
                            content = "New counter offer received by buyer on! <span>[" + prop_name + "]</span>"
                            add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id,
                                                notification_for=2, property_id=property_id, notification_type=6)
                
                # send email to buyer
                domain_url = subdomain_url.replace("###", domain_name) + "best-offers"
                template_data = {"domain_id": domain_id, "slug": "high_and_best_counter_offer_sent"}
                extra_data = {
                    "user_name": buyer_name.title(),
                    "name": agent_name.title(),
                    "email": agent_email,
                    "phone": phone_format(agent_phone),
                    "offer_price": number_format(offer_price),
                    "earnest_money_deposit": "$" + number_format(earnest_money_deposit) if property_detail.earnest_deposit_type == 1 else str(earnest_money_deposit) + "%",
                    "down_payment": number_format(down_payment),
                    "closing_date": closing_period_text[closing_period],
                    "message": comment,
                    "property_address": property_address,
                    "property_city": property_city,
                    "property_state": property_state,
                    "property_image": image_url,
                    "dashboard_link": domain_url,
                    "domain_id": domain_id
                }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                # send email to agent and broker
                template_data = {"domain_id": domain_id, "slug": "high_and_best_counter_offer_received"}
                domain_url = subdomain_url.replace("###",
                                                    domain_name) + "admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    "property_address": property_address,
                    "property_city": property_city,
                    "property_state": property_state,
                    "property_image": image_url,
                    "dashboard_link": domain_url,
                    "offer_price": number_format(offer_price),
                    "earnest_money_deposit": "$" + number_format(earnest_money_deposit) if property_detail.earnest_deposit_type == 1 else str(earnest_money_deposit) + "%",
                    "down_payment": number_format(down_payment),
                    "closing_date": closing_period_text[closing_period],
                    "message": comment,
                    "counter_by": 'buyer',
                    "domain_id": domain_id,
                    "name": buyer_name,
                    "email": buyer_email,
                    "phone": phone_format(buyer_phone)
                }
                if agent_email.lower() != buyer_email.lower():
                    extra_data['user_name'] = agent_name.title()
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                if broker_email.lower() != agent_email.lower():
                    extra_data['user_name'] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("LOI successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MakeLoiView(APIView):
    """
    Make LOI
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))
            max_dt = timezone.now()
            property_auction = PropertyAuction.objects.filter(property=property_id).first()
            if property_auction.status_id != 1:
                return Response(response.parsejson("Offer not active.", "", status=403))
            # property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt, end_date__gte=max_dt).first()
            property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lt=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer not started yet.", "", status=403))
            property_auction = PropertyAuction.objects.filter(property=property_id, end_date__gt=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer ended now.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "step" in data and data['step'] != "":
                step = int(data['step'])
            else:
                return Response(response.parsejson("step is required", "", status=403))

            if step == 1:
                if "first_name" in data and data['first_name'] != "":
                    first_name = data['first_name']
                else:
                    return Response(response.parsejson("first_name is required", "", status=403))

                if "last_name" in data and data['last_name'] != "":
                    last_name = data['last_name']
                else:
                    return Response(response.parsejson("last_name is required", "", status=403))

                if "email" in data and data['email'] != "":
                    email = data['email']
                else:
                    return Response(response.parsejson("email is required", "", status=403))

                if "address_first" in data and data['address_first'] != "":
                    address_first = data['address_first']
                else:
                    return Response(response.parsejson("address_first is required", "", status=403))

                if "city" in data and data['city'] != "":
                    city = data['city']
                else:
                    return Response(response.parsejson("city is required", "", status=403))

                if "state" in data and data['state'] != "":
                    state = int(data['state'])
                else:
                    return Response(response.parsejson("state is required", "", status=403))

                if "phone_no" in data and data['phone_no'] != "":
                    phone_no = data['phone_no']
                else:
                    return Response(response.parsejson("phone_no is required", "", status=403))

                if "postal_code" in data and data['postal_code'] != "":
                    postal_code = data['postal_code']
                else:
                    return Response(response.parsejson("postal_code is required", "", status=403))

                if "user_type" in data and data['user_type'] != "":
                    user_type = int(data['user_type'])
                else:
                    return Response(response.parsejson("user_type is required", "", status=403))

                if user_type == 2:
                    if "working_with_agent" in data and data['working_with_agent'] != "":
                        working_with_agent = int(data['working_with_agent'])
                    else:
                        return Response(response.parsejson("working_with_agent is required", "", status=403))
                else:
                    working_with_agent = None
                if (user_type == 2 and not working_with_agent) or (user_type == 4):
                    if "property_in_person" in data and data['property_in_person'] != "":
                        property_in_person = int(data['property_in_person'])
                    else:
                        return Response(response.parsejson("property_in_person is required", "", status=403))

                    if "pre_qualified_lender" in data and data['pre_qualified_lender'] != "":
                        pre_qualified_lender = int(data['pre_qualified_lender'])
                    else:
                        return Response(response.parsejson("pre_qualified_lender is required", "", status=403))

                behalf_of_buyer = None
                if "behalf_of_buyer" in data and data['behalf_of_buyer'] != "":
                    behalf_of_buyer = int(data['behalf_of_buyer'])

                if behalf_of_buyer is not None and behalf_of_buyer == 1:
                    if "buyer_first_name" in data and data['buyer_first_name'] != "":
                        buyer_first_name = data['buyer_first_name']
                    else:
                        return Response(response.parsejson("buyer_first_name is required", "", status=403))

                    if "buyer_last_name" in data and data['buyer_last_name'] != "":
                        buyer_last_name = data['buyer_last_name']
                    else:
                        return Response(response.parsejson("buyer_last_name is required", "", status=403))

                    if "buyer_email" in data and data['buyer_email'] != "":
                        buyer_email = data['buyer_email']
                    else:
                        return Response(response.parsejson("buyer_email is required", "", status=403))

                    buyer_company = None
                    if "buyer_company" in data and data['buyer_company'] != "":
                        buyer_company = data['buyer_company']

                    if "buyer_phone_no" in data and data['buyer_phone_no'] != "":
                        buyer_phone_no = data['buyer_phone_no']
                    else:
                        return Response(response.parsejson("buyer_phone_no is required", "", status=403))
            elif step == 2:
                if "offer_price" in data and data['offer_price'] != "":
                    offer_price = data['offer_price']
                else:
                    return Response(response.parsejson("offer_price is required", "", status=403))

                if "earnest_money_deposit" in data and data['earnest_money_deposit'] != "":
                    earnest_money_deposit = data['earnest_money_deposit']
                    # if float(earnest_money_deposit) > property_auction.start_price:
                    #     return Response(response.parsejson(
                    #         "earnest_money_deposit should be less or equal to " + str(property_auction.start_price), "",
                    #         status=403))
                    #
                    # if float(earnest_money_deposit) < property_listing.earnest_deposit:
                    #     return Response(response.parsejson("earnest_money_deposit should be greater or equal to " + str(
                    #         property_listing.earnest_deposit), "", status=403))
                else:
                    return Response(response.parsejson("earnest_money_deposit is required", "", status=403))

                if "down_payment" in data and data['down_payment'] != "":
                    down_payment = data['down_payment']
                else:
                    return Response(response.parsejson("down_payment is required", "", status=403))

                if "due_diligence_period" in data and data['due_diligence_period'] != "":
                    due_diligence_period = int(data['due_diligence_period'])
                    # if due_diligence_period > property_listing.due_diligence_period:
                    #     return Response(response.parsejson("due_diligence_period should be less or equal to " + str(property_listing.due_diligence_period), "", status=403))
                else:
                    return Response(response.parsejson("due_diligence_period is required", "", status=403))

                if "closing_period" in data and data['closing_period'] != "":
                    closing_period = int(data['closing_period'])
                    if closing_period > property_listing.escrow_period:
                        return Response(response.parsejson(
                            "closing_period should be less or equal to " + str(property_listing.escrow_period), "",
                            status=403))
                else:
                    return Response(response.parsejson("closing_period is required", "", status=403))

                if "financing" in data and data['financing'] != "":
                    financing = int(data['financing'])
                else:
                    return Response(response.parsejson("financing is required", "", status=403))

                if "offer_contingent" in data and data['offer_contingent'] != "":
                    offer_contingent = int(data['offer_contingent'])
                else:
                    return Response(response.parsejson("offer_contingent is required", "", status=403))

                if "sale_contingency" in data and data['sale_contingency'] != "":
                    sale_contingency = int(data['sale_contingency'])
                else:
                    return Response(response.parsejson("sale_contingency is required", "", status=403))

                if "appraisal_contingent" in data and data['appraisal_contingent'] != "":
                    appraisal_contingent = int(data['appraisal_contingent'])
                else:
                    return Response(response.parsejson("appraisal_contingent is required", "", status=403))

                if "closing_cost" in data and data['closing_cost'] != "":
                    closing_cost = int(data['closing_cost'])
                else:
                    return Response(response.parsejson("closing_cost is required", "", status=403))
            elif step == 3:
                document_id = None
                if "document_id" in data and type(data['document_id']) == list and len(data['document_id']) > 0:
                    document_id = data['document_id']

                comments = None
                if "offer_comment" in data and data['offer_comment'] != "":
                    comments = data['offer_comment']
            elif step == 4:
                if "terms" in data and data['terms'] != "":
                    terms = int(data['terms'])
                    if terms != 1:
                        return Response(response.parsejson("Please accept term.", "", status=403))
                else:
                    return Response(response.parsejson("terms is required", "", status=403))

            master_offer = MasterOffer.objects.filter(property=property_id, domain=domain_id, user=user_id).last()
            negotiation_id = None
            if master_offer is not None:
                negotiation_id = master_offer.id
            if step == 1:
                if master_offer is None:
                    master_offer = MasterOffer()
                    master_offer.domain_id = domain_id
                    master_offer.property_id = property_id
                    master_offer.user_id = user_id
                    master_offer.user_type = user_type
                    master_offer.working_with_agent = working_with_agent
                    master_offer.property_in_person = property_in_person
                    master_offer.pre_qualified_lender = pre_qualified_lender
                    master_offer.status_id = 1
                    master_offer.behalf_of_buyer = behalf_of_buyer
                    master_offer.save()
                    negotiation_id = master_offer.id

                    offer_address = OfferAddress()
                    offer_address.domain_id = domain_id
                    offer_address.master_offer_id = negotiation_id
                    offer_address.first_name = first_name
                    offer_address.last_name = last_name
                    offer_address.email = email
                    offer_address.address_first = address_first
                    offer_address.city = city
                    offer_address.state_id = state
                    offer_address.phone_no = phone_no
                    offer_address.postal_code = postal_code
                    offer_address.user_id = user_id
                    offer_address.status_id = 1
                    if behalf_of_buyer is not None and behalf_of_buyer == 1:
                        offer_address.buyer_first_name = buyer_first_name
                        offer_address.buyer_last_name = buyer_last_name
                        offer_address.buyer_email = buyer_email
                        offer_address.buyer_company = buyer_company
                        offer_address.buyer_phone_no = buyer_phone_no
                    offer_address.save()
                else:
                    if master_offer.is_canceled == 1 or master_offer.is_declined == 1:
                        master_offer.is_canceled = 0
                        master_offer.is_declined = 0
                        master_offer.status_id = 1
                        master_offer.declined_by_id = None
                        master_offer.final_by = None
                    master_offer.user_type = user_type
                    master_offer.working_with_agent = working_with_agent
                    master_offer.property_in_person = property_in_person
                    master_offer.pre_qualified_lender = pre_qualified_lender
                    master_offer.behalf_of_buyer = behalf_of_buyer
                    master_offer.save()

                    offer_address = OfferAddress.objects.filter(master_offer=negotiation_id).first()
                    if offer_address is None:
                        offer_address = OfferAddress()
                        offer_address.domain_id = domain_id
                        offer_address.master_offer_id = negotiation_id
                        offer_address.user_id = user_id
                    offer_address.first_name = first_name
                    offer_address.last_name = last_name
                    offer_address.email = email
                    offer_address.address_first = address_first
                    offer_address.city = city
                    offer_address.state_id = state
                    offer_address.phone_no = phone_no
                    offer_address.postal_code = postal_code
                    offer_address.status_id = 1
                    if behalf_of_buyer is not None and behalf_of_buyer == 1:
                        offer_address.buyer_first_name = buyer_first_name
                        offer_address.buyer_last_name = buyer_last_name
                        offer_address.buyer_email = buyer_email
                        offer_address.buyer_company = buyer_company
                        offer_address.buyer_phone_no = buyer_phone_no
                    else:
                        offer_address.buyer_first_name = None
                        offer_address.buyer_last_name = None
                        offer_address.buyer_email = None
                        offer_address.buyer_company = None
                        offer_address.buyer_phone_no = None
                    offer_address.save()
            elif step == 2:
                offer_detail = OfferDetail.objects.filter(master_offer=negotiation_id).first()
                if offer_detail is None:
                    offer_detail = OfferDetail()
                    offer_detail.domain_id = domain_id
                    offer_detail.master_offer_id = negotiation_id
                    offer_detail.user_id = user_id
                    offer_detail.status_id = 1
                offer_detail.earnest_money_deposit = earnest_money_deposit
                offer_detail.down_payment = down_payment
                offer_detail.due_diligence_period = due_diligence_period
                offer_detail.closing_period = closing_period
                offer_detail.financing = financing
                offer_detail.offer_contingent = offer_contingent
                offer_detail.sale_contingency = sale_contingency
                offer_detail.appraisal_contingent = appraisal_contingent
                offer_detail.closing_cost = closing_cost
                offer_detail.save()

                negotiated_offers = NegotiatedOffers.objects.filter(master_offer=negotiation_id, user=user_id, status=1, offer_by=1).last()
                if negotiated_offers is None or negotiated_offers.offer_price != offer_price:
                    negotiated_offers = NegotiatedOffers()
                    negotiated_offers.domain_id = domain_id
                    negotiated_offers.property_id = property_id
                    negotiated_offers.master_offer_id = negotiation_id
                    negotiated_offers.user_id = user_id
                    negotiated_offers.offer_by = 1
                    negotiated_offers.display_status = 1
                    negotiated_offers.offer_price = offer_price
                    negotiated_offers.status_id = 1
                    negotiated_offers.save()
            elif step == 3:
                if document_id is not None and len(document_id) > 0:
                    OfferDocuments.objects.filter(master_offer=negotiation_id).delete()
                    for document in document_id:
                        offer_documents = OfferDocuments()
                        offer_documents.domain_id = domain_id
                        offer_documents.property_id = property_id
                        offer_documents.master_offer_id = negotiation_id
                        offer_documents.document_id = document
                        offer_documents.status_id = 1
                        offer_documents.save()
                MasterOffer.objects.filter(id=negotiation_id).update(document_comment=comments)
            elif step == 4:
                MasterOffer.objects.filter(id=negotiation_id).update(terms=terms)

            if negotiation_id is not None:
                MasterOffer.objects.filter(id=negotiation_id).update(steps=step)

            try:           
                if step == 4:
                    # ----------------Notifications-----------
                    negotiated_offers = NegotiatedOffers.objects.filter(master_offer=negotiation_id, user=user_id, status=1, offer_by=1).last()
                    prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                    
                    if negotiated_offers.count() <= 0:
                        title = "Highest & Best offer"
                        content = "You Made Highest and Best Offer <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                        title = "Highest & Best offer"
                        content = "You Received an Offer! <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
                    else:
                        title = "Highest & Best Counter offer"
                        content = "You Made a Counter-Offer <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                        title = "Highest & Best Counter offer"
                        content = "A Buyer Sent you a Counter-Offer! <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                    property_detail = negotiated_offers.property
                    broker_detail = Users.objects.get(site_id=domain_id)
                    broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                    broker_email = broker_detail.email if broker_detail.email is not None else ""
                    broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                    agent_detail = negotiated_offers.property.agent
                    agent_email = agent_detail.email if agent_detail.email is not None else ""
                    agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                    agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                    buyer_detail = negotiated_offers.user
                    buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                    buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                    buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                    property_address = property_detail.address_one if property_detail.address_one is not None else ""
                    property_city = property_detail.city if property_detail.city is not None else ""
                    property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                    domain_name = network.domain_name
                    subdomain_url = settings.SUBDOMAIN_URL
                    loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                    # web_url = settings.FRONT_BASE_URL
                    # image_url = web_url+'/static/admin/images/property-default-img.png'
                    # upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                    # comment = ''
                    # if upload is not None:
                    #     image = upload.upload.doc_file_name
                    #     bucket_name = upload.upload.bucket_name
                    #     image_url = settings.AWS_URL+bucket_name+'/'+image

                    #send to buyer
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_buyer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": broker_name,
                        "email": broker_email,
                        "phone": phone_format(broker_phone),
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    #send to agent and broker
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_seller"}
                    extra_data = {
                        "domain_id": domain_id,
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": buyer_name,
                        "email": buyer_email,
                        "phone": phone_format(buyer_phone)
                    }
                    if agent_email.lower() != buyer_email.lower():
                        extra_data['user_name'] = agent_name
                        compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                    if broker_email.lower() != agent_email.lower():
                        extra_data['user_name'] = broker_name
                        compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                
            except:
                pass
            return Response(response.parsejson("LOI successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedMakeLoiView(APIView):
    """
    Enhanced Make LOI
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1,
                                                                  status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            max_dt = timezone.now()
            property_auction = PropertyAuction.objects.filter(property=property_id).first()
            if property_auction.status_id != 1:
                return Response(response.parsejson("Offer not active.", "", status=403))
            # property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt, end_date__gte=max_dt).first()
            property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lt=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer not started yet.", "", status=403))
            master_offer_details = MasterOffer.objects.filter(property=property_id, domain=domain_id, user=user_id, status=1, is_declined=0).last()
            if master_offer_details is None:
                property_auction = PropertyAuction.objects.filter(property=property_id, end_date__gt=max_dt).first()
                if property_auction is None:
                    return Response(response.parsejson("Offer ended now.", "", status=403))

            if "step" in data and data['step'] != "":
                step = int(data['step'])
            else:
                return Response(response.parsejson("step is required", "", status=403))
            
            master_offer_count = MasterOffer.objects.filter(property=property_id, accepted_by__isnull=False).count()
            if master_offer_count:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            if step == 1:
                if "first_name" in data and data['first_name'] != "":
                    first_name = data['first_name']
                else:
                    return Response(response.parsejson("first_name is required", "", status=403))

                if "last_name" in data and data['last_name'] != "":
                    last_name = data['last_name']
                else:
                    return Response(response.parsejson("last_name is required", "", status=403))

                if "email" in data and data['email'] != "":
                    email = data['email']
                else:
                    return Response(response.parsejson("email is required", "", status=403))

                if "address_first" in data and data['address_first'] != "":
                    address_first = data['address_first']
                else:
                    return Response(response.parsejson("address_first is required", "", status=403))

                if "city" in data and data['city'] != "":
                    city = data['city']
                else:
                    return Response(response.parsejson("city is required", "", status=403))

                if "state" in data and data['state'] != "":
                    state = int(data['state'])
                else:
                    return Response(response.parsejson("state is required", "", status=403))

                if "phone_no" in data and data['phone_no'] != "":
                    phone_no = data['phone_no']
                else:
                    return Response(response.parsejson("phone_no is required", "", status=403))

                if "postal_code" in data and data['postal_code'] != "":
                    postal_code = data['postal_code']
                else:
                    return Response(response.parsejson("postal_code is required", "", status=403))

                if "user_type" in data and data['user_type'] != "":
                    user_type = int(data['user_type'])
                else:
                    return Response(response.parsejson("user_type is required", "", status=403))

                if "country" in data and data['country'] != "":
                    country = int(data['country'])
                else:
                    country = None

                if user_type == 2:
                    if "working_with_agent" in data and data['working_with_agent'] != "":
                        working_with_agent = int(data['working_with_agent'])
                    else:
                        return Response(response.parsejson("working_with_agent is required", "", status=403))
                else:
                    working_with_agent = None
                if (user_type == 2 and not working_with_agent) or (user_type == 4):
                    if "property_in_person" in data and data['property_in_person'] != "":
                        property_in_person = int(data['property_in_person'])
                    else:
                        return Response(response.parsejson("property_in_person is required", "", status=403))

                    if "pre_qualified_lender" in data and data['pre_qualified_lender'] != "":
                        pre_qualified_lender = int(data['pre_qualified_lender'])
                    else:
                        return Response(response.parsejson("pre_qualified_lender is required", "", status=403))

                behalf_of_buyer = None
                if "behalf_of_buyer" in data and data['behalf_of_buyer'] != "":
                    behalf_of_buyer = int(data['behalf_of_buyer'])

                if behalf_of_buyer is not None and behalf_of_buyer == 1:
                    if "buyer_first_name" in data and data['buyer_first_name'] != "":
                        buyer_first_name = data['buyer_first_name']
                    else:
                        return Response(response.parsejson("buyer_first_name is required", "", status=403))

                    if "buyer_last_name" in data and data['buyer_last_name'] != "":
                        buyer_last_name = data['buyer_last_name']
                    else:
                        return Response(response.parsejson("buyer_last_name is required", "", status=403))

                    if "buyer_email" in data and data['buyer_email'] != "":
                        buyer_email = data['buyer_email']
                    else:
                        return Response(response.parsejson("buyer_email is required", "", status=403))

                    buyer_company = None
                    if "buyer_company" in data and data['buyer_company'] != "":
                        buyer_company = data['buyer_company']

                    if "buyer_phone_no" in data and data['buyer_phone_no'] != "":
                        buyer_phone_no = data['buyer_phone_no']
                    else:
                        return Response(response.parsejson("buyer_phone_no is required", "", status=403))
            elif step == 2:
                if "offer_price" in data and data['offer_price'] != "":
                    offer_price = data['offer_price']
                else:
                    return Response(response.parsejson("offer_price is required", "", status=403))

                if "earnest_money_deposit" in data and data['earnest_money_deposit'] != "":
                    earnest_money_deposit = data['earnest_money_deposit']
                    # if float(earnest_money_deposit) > property_auction.start_price:
                    #     return Response(response.parsejson(
                    #         "earnest_money_deposit should be less or equal to " + str(property_auction.start_price), "",
                    #         status=403))
                    #
                    # if float(earnest_money_deposit) < property_listing.earnest_deposit:
                    #     return Response(response.parsejson("earnest_money_deposit should be greater or equal to " + str(
                    #         property_listing.earnest_deposit), "", status=403))
                else:
                    return Response(response.parsejson("earnest_money_deposit is required", "", status=403))

                if "down_payment" in data and data['down_payment'] != "":
                    down_payment = data['down_payment']
                else:
                    return Response(response.parsejson("down_payment is required", "", status=403))

                if "due_diligence_period" in data and data['due_diligence_period'] != "":
                    due_diligence_period = int(data['due_diligence_period'])
                    # if due_diligence_period > property_listing.due_diligence_period:
                    #     return Response(response.parsejson("due_diligence_period should be less or equal to " + str(property_listing.due_diligence_period), "", status=403))
                else:
                    return Response(response.parsejson("due_diligence_period is required", "", status=403))

                if "closing_period" in data and data['closing_period'] != "":
                    closing_period = int(data['closing_period'])
                    if property_listing.escrow_period is not None and closing_period > property_listing.escrow_period:
                        return Response(response.parsejson("closing_period should be less or equal to " + str(property_listing.escrow_period), "", status=403))
                else:
                    return Response(response.parsejson("closing_period is required", "", status=403))

                if "financing" in data and data['financing'] != "":
                    financing = int(data['financing'])
                else:
                    return Response(response.parsejson("financing is required", "", status=403))

                if "offer_contingent" in data and data['offer_contingent'] != "":
                    offer_contingent = int(data['offer_contingent'])
                else:
                    return Response(response.parsejson("offer_contingent is required", "", status=403))

                if "sale_contingency" in data and data['sale_contingency'] != "":
                    sale_contingency = int(data['sale_contingency'])
                else:
                    return Response(response.parsejson("sale_contingency is required", "", status=403))

                if "appraisal_contingent" in data and data['appraisal_contingent'] != "":
                    appraisal_contingent = int(data['appraisal_contingent'])
                else:
                    return Response(response.parsejson("appraisal_contingent is required", "", status=403))

                if "closing_cost" in data and data['closing_cost'] != "":
                    closing_cost = int(data['closing_cost'])
                else:
                    return Response(response.parsejson("closing_cost is required", "", status=403))
            elif step == 3:
                document_id = None
                if "document_id" in data and type(data['document_id']) == list and len(data['document_id']) > 0:
                    document_id = data['document_id']

                comments = None
                if "offer_comment" in data and data['offer_comment'] != "":
                    comments = data['offer_comment']
            elif step == 4:
                if "terms" in data and data['terms'] != "":
                    terms = int(data['terms'])
                    if terms != 1:
                        return Response(response.parsejson("Please accept term.", "", status=403))
                else:
                    return Response(response.parsejson("terms is required", "", status=403))

            master_offer = MasterOffer.objects.filter(property=property_id, domain=domain_id, user=user_id).last()
            negotiation_id = None
            if master_offer is not None:
                negotiation_id = master_offer.id
            if step == 1:
                if master_offer is None:
                    master_offer = MasterOffer()
                    master_offer.domain_id = domain_id
                    master_offer.property_id = property_id
                    master_offer.user_id = user_id
                    master_offer.user_type = user_type
                    master_offer.working_with_agent = working_with_agent
                    master_offer.property_in_person = property_in_person
                    master_offer.pre_qualified_lender = pre_qualified_lender
                    master_offer.status_id = 2
                    master_offer.behalf_of_buyer = behalf_of_buyer
                    master_offer.save()
                    negotiation_id = master_offer.id

                    offer_address = OfferAddress()
                    offer_address.domain_id = domain_id
                    offer_address.master_offer_id = negotiation_id
                    offer_address.first_name = first_name
                    offer_address.last_name = last_name
                    offer_address.email = email
                    offer_address.address_first = address_first
                    offer_address.city = city
                    offer_address.country_id = country
                    offer_address.state_id = state
                    offer_address.phone_no = phone_no
                    offer_address.postal_code = postal_code
                    offer_address.user_id = user_id
                    offer_address.status_id = 1
                    if behalf_of_buyer is not None and behalf_of_buyer == 1:
                        offer_address.buyer_first_name = buyer_first_name
                        offer_address.buyer_last_name = buyer_last_name
                        offer_address.buyer_email = buyer_email
                        offer_address.buyer_company = buyer_company
                        offer_address.buyer_phone_no = buyer_phone_no
                    offer_address.save()
                else:
                    if master_offer.is_canceled == 1 or master_offer.is_declined == 1:
                        master_offer.is_canceled = 0
                        master_offer.is_declined = 0
                        master_offer.status_id = 1
                        master_offer.declined_by_id = None
                        master_offer.final_by = None
                        master_offer.declined_reason = None
                    master_offer.user_type = user_type
                    master_offer.working_with_agent = working_with_agent
                    master_offer.property_in_person = property_in_person
                    master_offer.pre_qualified_lender = pre_qualified_lender
                    master_offer.behalf_of_buyer = behalf_of_buyer
                    master_offer.save()

                    offer_address = OfferAddress.objects.filter(master_offer=negotiation_id).first()
                    if offer_address is None:
                        offer_address = OfferAddress()
                        offer_address.domain_id = domain_id
                        offer_address.master_offer_id = negotiation_id
                        offer_address.user_id = user_id
                    offer_address.first_name = first_name
                    offer_address.last_name = last_name
                    offer_address.email = email
                    offer_address.address_first = address_first
                    offer_address.city = city
                    offer_address.country_id = country
                    offer_address.state_id = state
                    offer_address.phone_no = phone_no
                    offer_address.postal_code = postal_code
                    offer_address.status_id = 1
                    if behalf_of_buyer is not None and behalf_of_buyer == 1:
                        offer_address.buyer_first_name = buyer_first_name
                        offer_address.buyer_last_name = buyer_last_name
                        offer_address.buyer_email = buyer_email
                        offer_address.buyer_company = buyer_company
                        offer_address.buyer_phone_no = buyer_phone_no
                    else:
                        offer_address.buyer_first_name = None
                        offer_address.buyer_last_name = None
                        offer_address.buyer_email = None
                        offer_address.buyer_company = None
                        offer_address.buyer_phone_no = None
                    offer_address.save()
            elif step == 2:
                # offer_detail = OfferDetail.objects.filter(master_offer=negotiation_id).first()
                # if offer_detail is None:
                #     offer_detail = OfferDetail()
                #     offer_detail.domain_id = domain_id
                #     offer_detail.master_offer_id = negotiation_id
                #     offer_detail.user_id = user_id
                #     offer_detail.status_id = 1
                # offer_detail.earnest_money_deposit = earnest_money_deposit
                # offer_detail.down_payment = down_payment
                # offer_detail.due_diligence_period = due_diligence_period
                # offer_detail.closing_period = closing_period
                # offer_detail.financing = financing
                # offer_detail.offer_contingent = offer_contingent
                # offer_detail.sale_contingency = sale_contingency
                # offer_detail.appraisal_contingent = appraisal_contingent
                # offer_detail.closing_cost = closing_cost
                # offer_detail.save()

                # negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=negotiation_id, user=user_id, status=1, offer_by=1).last()
                # if negotiated_offers is None or negotiated_offers.offer_price != offer_price:
                #     negotiated_offers = HighestBestNegotiatedOffers()
                #     negotiated_offers.domain_id = domain_id
                #     negotiated_offers.property_id = property_id
                #     negotiated_offers.master_offer_id = negotiation_id
                #     negotiated_offers.user_id = user_id
                #     negotiated_offers.offer_by = 1
                #     negotiated_offers.display_status = 1
                #     negotiated_offers.status_id = 1
                # negotiated_offers.offer_price = offer_price
                # negotiated_offers.earnest_money_deposit = earnest_money_deposit
                # negotiated_offers.down_payment = down_payment
                # negotiated_offers.due_diligence_period = due_diligence_period
                # negotiated_offers.closing_period = closing_period
                # negotiated_offers.financing = financing
                # negotiated_offers.offer_contingent = offer_contingent
                # negotiated_offers.sale_contingency = sale_contingency
                # negotiated_offers.appraisal_contingent = appraisal_contingent
                # negotiated_offers.closing_cost = closing_cost
                # negotiated_offers.save()
                negotiated_offers = HighestBestNegotiatedOffers()
                negotiated_offers.domain_id = domain_id
                negotiated_offers.property_id = property_id
                negotiated_offers.master_offer_id = negotiation_id
                negotiated_offers.user_id = user_id
                negotiated_offers.offer_by = 1
                negotiated_offers.display_status = 1
                # negotiated_offers.status_id = 1
                negotiated_offers.status_id = 2
                negotiated_offers.offer_price = offer_price
                negotiated_offers.earnest_money_deposit = earnest_money_deposit
                negotiated_offers.down_payment = down_payment
                negotiated_offers.due_diligence_period = due_diligence_period
                negotiated_offers.closing_period = closing_period
                negotiated_offers.financing = financing
                negotiated_offers.offer_contingent = offer_contingent
                negotiated_offers.sale_contingency = sale_contingency
                negotiated_offers.appraisal_contingent = appraisal_contingent
                negotiated_offers.closing_cost = closing_cost
                negotiated_offers.save()
            elif step == 3:
                if document_id is not None and len(document_id) > 0:
                    OfferDocuments.objects.filter(master_offer=negotiation_id).delete()
                    for document in document_id:
                        offer_documents = OfferDocuments()
                        offer_documents.domain_id = domain_id
                        offer_documents.property_id = property_id
                        offer_documents.master_offer_id = negotiation_id
                        offer_documents.document_id = document
                        offer_documents.status_id = 1
                        offer_documents.save()
                MasterOffer.objects.filter(id=negotiation_id).update(document_comment=comments)
                highest_best_negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=negotiation_id).last()
                highest_best_negotiated_offers.comments = comments
                highest_best_negotiated_offers.save()
            elif step == 4:
                MasterOffer.objects.filter(id=negotiation_id).update(terms=terms, status=1)
                update_negotiated = HighestBestNegotiatedOffers.objects.filter(master_offer=negotiation_id).last()
                update_negotiated.status_id = 1
                update_negotiated.save()

            if negotiation_id is not None:
                MasterOffer.objects.filter(id=negotiation_id).update(steps=step)

            try:
                if step == 4:
                    negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=negotiation_id, user=user_id, status=1, offer_by=1).last()
                    property_detail = negotiated_offers.property
                    broker_detail = Users.objects.get(site_id=domain_id)
                    broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                    broker_email = broker_detail.email if broker_detail.email is not None else ""
                    broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                    agent_detail = negotiated_offers.property.agent
                    agent_email = agent_detail.email if agent_detail.email is not None else ""
                    agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                    agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                    buyer_detail = negotiated_offers.user
                    buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                    buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                    buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                    property_address = property_detail.address_one if property_detail.address_one is not None else ""
                    property_city = property_detail.city if property_detail.city is not None else ""
                    property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                    domain_name = network.domain_name
                    subdomain_url = settings.SUBDOMAIN_URL
                    loi_url = subdomain_url.replace("###", domain_name) + "submit-loi/?property_id=" + str(property_id)


                    # ----------------Notifications-----------
                    prop_name = property_detail.address_one if property_detail.address_one else property_detail.id

                    title = "Highest & Best offer"
                    content = "You Made Highest and Best Offer <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=user_id, added_by=user_id,
                                        notification_for=1, property_id=property_id)

                    if agent_email.lower() != buyer_email.lower():
                        content = "You Received an Offer! <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id,
                                            notification_for=2, property_id=property_id, notification_type=6)

                    if broker_email.lower() != agent_email.lower():
                        content = "New offer received on! <span>[" + prop_name + "]</span>"
                        add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id,
                                            notification_for=2, property_id=property_id, notification_type=6)
                        
                    # web_url = settings.FRONT_BASE_URL
                    # image_url = web_url+'/static/admin/images/property-default-img.png'
                    # upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                    # comment = ''
                    # if upload is not None:
                    #     image = upload.upload.doc_file_name
                    #     bucket_name = upload.upload.bucket_name
                    #     image_url = settings.AWS_URL+bucket_name+'/'+image

                    # send to buyer
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_buyer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": broker_name,
                        "email": broker_email,
                        "phone": phone_format(broker_phone),
                        "loi_link": loi_url,
                        "offer_price": '$' + number_format(negotiated_offers.offer_price)
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send to agent and broker
                    template_data = {"domain_id": domain_id, "slug": "highest_and_best_offer_seller"}
                    extra_data = {
                        "domain_id": domain_id,
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "name": buyer_name,
                        "email": buyer_email,
                        "phone": phone_format(buyer_phone),
                        "offer_price": '$' + number_format(negotiated_offers.offer_price)
                    }
                    if agent_email.lower() != buyer_email.lower():
                        extra_data['user_name'] = agent_name
                        compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                    if broker_email.lower() != agent_email.lower():
                        extra_data['user_name'] = broker_name
                        compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass
            return Response(response.parsejson("Highest and best offer successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetLoiView(APIView):
    """
    Get loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            # user = Users.objects.get(id=user_id)
            # serializer = BestFinalDetailSerializer(user, context=property_id)
            master_offer = MasterOffer.objects.filter(domain=domain, property=property_id, user=user_id).first()
            serializer = GetLoiSerializer(master_offer)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidDelete(APIView):
    """
    Bid delete
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, is_agent=1, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[1]).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            bid = Bid.objects.filter(domain=domain, property=property_id, is_canceled=0).last()
            if bid is None:
                return Response(response.parsejson("No bid exist for delete.", "", status=201))
            bid.delete()
            property_auction = PropertyAuction.objects.filter(domain=domain, property=property_id).first()
            all_data = {"auction_id": property_auction.id, "property_id": property_id}
            return Response(response.parsejson("Bid deleted successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendLoiView(APIView):
    """
    Send Loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, site=domain, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, is_agent=1, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7]).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id).first()
            serializer = SendLoiSerializer(master_offer)
            notification_template = NotificationTemplate.objects.filter(Q(event__slug='offer_loi') & Q(site=domain) & Q(status=1)).first()
            if notification_template is None:
                notification_template = NotificationTemplate.objects.filter(Q(event__slug='offer_loi') & Q(site__isnull=True) & Q(status=1)).first()
            extra = {"domain_id": domain, "message": message, "domain_name": network.domain_name}
            send_custom_email(to_email=[email], template_id=notification_template.id, subject="Offer Document", extra=extra, attachment=serializer.data)
            return Response(response.parsejson("Send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerAcceptLoiView(APIView):
    """
    Buyer accept loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 1:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            elif negotiated_offers.best_offer_is_accept == 1:
                return Response(response.parsejson("Offer already accepted.", "", status=403))
            # --------------Update Offer------------
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.display_status = 3
            negotiated_offers.save()


            try:

                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Highest & Best offer accepted"
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best offer accepted"
                content = "Buyer accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                title = "Property sold"
                content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                # ===========Send Email===========================
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = negotiated_offers.user.first_name
                buyer_email = negotiated_offers.user.email
                # agent_email = property_detail.agent.email
                # agent_name = property_detail.agent.first_name
                # agent_phone = property_detail.agent.phone_no
                # accept_detail = negotiated_offers.best_offer_accept_by
                # accept_email = accept_detail.email if accept_detail.email is not None else ""
                # accept_name = accept_detail.first_name if accept_detail.first_name is not None else ""
                # accept_phone = accept_detail.phone_no if accept_detail.phone_no is not None else ""
                # web_url = settings.FRONT_BASE_URL
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                current_neg_id = negotiated_offers.id

                # if int(sale_by_type) == 7:
                #     domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                # else:
                #     domain_url = subdomain_url.replace("###", domain_name)+"my-offers"

                # check property uploads
                # image_url = web_url+'/static/admin/images/property-default-img.png'
                # upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                # if upload is not None:
                #     image = upload.upload.doc_file_name
                #     bucket_name = upload.upload.bucket_name
                #     image_url = settings.AWS_URL+bucket_name+'/'+image
                # if agent_email.lower() == buyer_email.lower():
                #     accepted_by = 'buyer'
                #     extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                #     compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                # else:
                #     accepted_by = 'buyer'
                #     extra_data = {"user_name": buyer_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                #     compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                #     #================Email send property agent======================
                #     if int(sale_by_type) == 7:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                #     else:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                #     extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                #     compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    #================Email send broker agent======================
                # if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                #     if int(sale_by_type) == 7:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                #     else:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                #     extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": buyer_name, "email": buyer_email, "phone": phone_format(buyer_phone)}
                #     compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                
                
            
                # get all last offer by buyers
                all_offers = NegotiatedOffers.objects\
                    .filter(status=1, property=property_id, best_offer_is_accept=1)\
                    .order_by('user_id', '-added_on')\
                    .distinct('user_id')\
                    .values_list('id', flat=True)
            
                all_offers = NegotiatedOffers.objects\
                    .filter(id__in=all_offers)\
                    .order_by('-added_on')
                
                
                # find max offer price
                max_offers = NegotiatedOffers.objects\
                            .filter(id__in=all_offers.values_list('id', flat=True))\
                            .order_by('-offer_price')
                try:
                    higest_offer = max_offers[0]
                except:
                    higest_offer = None
                
                try:
                    second_higest_offer = max_offers[1]
                except:
                    second_higest_offer = None

                
                
                # check if this offer is highest or outbid
                negotiated_offers = all_offers.filter(master_offer=negotiation_id)[0]
                if  higest_offer and negotiated_offers.id == higest_offer.id:
                    # send high offer email
                    template_data = {"domain_id": domain_id, "slug": "loi_high_offer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "dashbaord_link": subdomain_url.replace("###", domain_name)+'best-offers/'
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send outbid loi email to recent high bidder
                    if second_higest_offer:
                        template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": second_higest_offer.user.first_name if second_higest_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": second_higest_offer.offer_price,
                            "loi_link": loi_url
                        }
                        compose_email(to_email=[second_higest_offer.user.email], template_data=template_data, extra_data=extra_data)   
                else:
                    # check if this user was last higest bidder
                    last_high_offers = NegotiatedOffers.objects\
                        .filter(status=1, property=property_id, best_offer_is_accept=1)\
                        .exclude(id=current_neg_id)\
                        .order_by("-offer_price").last()

                    if last_high_offers.user_id == master_offer.user_id:
                        # send high offer email
                        template_data = {"domain_id": domain_id, "slug": "loi_is_the_high_offer"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": higest_offer.user.first_name if higest_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": higest_offer.offer_price,
                            "dashbaord_link": subdomain_url.replace("###", domain_name)+'asset-details/?property_id='+property_id
                        }
                        compose_email(to_email=[higest_offer.user.email], template_data=template_data, extra_data=extra_data)
                    # send outbid email
                    template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": negotiated_offers.user.first_name if negotiated_offers.user.first_name is not None else "",
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[negotiated_offers.user.email], template_data=template_data, extra_data=extra_data)   
            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBuyerAcceptLoiView(APIView):
    """
    Enhanced Buyer accept loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7], is_approved=1,
                                                                  status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (
                            Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 1:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            elif negotiated_offers.best_offer_is_accept == 1:
                return Response(response.parsejson("Offer already accepted.", "", status=403))
            # --------------Update Offer------------
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.display_status = 3
            negotiated_offers.save()

            try:

                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = negotiated_offers.master_offer.user.first_name
                buyer_email = negotiated_offers.master_offer.user.email
                # agent_email = property_detail.agent.email
                # agent_name = property_detail.agent.first_name
                # agent_phone = property_detail.agent.phone_no
                # accept_detail = negotiated_offers.best_offer_accept_by
                # accept_email = accept_detail.email if accept_detail.email is not None else ""
                # accept_name = accept_detail.first_name if accept_detail.first_name is not None else ""
                # accept_phone = accept_detail.phone_no if accept_detail.phone_no is not None else ""
                # web_url = settings.FRONT_BASE_URL
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                loi_url = subdomain_url.replace("###", domain_name) + "submit-loi/?property_id=" + str(property_id)
                current_neg_id = negotiated_offers.id

                # ----------------Notifications-----------
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id

                title = "Highest & Best offer accepted"
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1,
                                 property_id=property_id)

                if user_id != agent_id:
                    content = "Buyer accepted your offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)
                
                if agent_id != broker_detail.id:
                    content = "Buyer accepted an offer on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)


                # ===========Send Email===========================

                # get all last offer by buyers
                all_offers = HighestBestNegotiatedOffers.objects \
                    .filter(status=1, is_declined=0, property=property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                    .order_by('master_offer_id', '-added_on') \
                    .distinct('master_offer_id') \
                    .values_list('id', flat=True)

                all_offers = HighestBestNegotiatedOffers.objects \
                    .filter(id__in=all_offers) \
                    .order_by('-added_on')

                # find max offer price
                max_offers = HighestBestNegotiatedOffers.objects \
                    .filter(id__in=all_offers.values_list('id', flat=True)) \
                    .order_by('-offer_price')
                try:
                    higest_offer = max_offers[0]
                except:
                    higest_offer = None

                try:
                    second_higest_offer = max_offers[1]
                except:
                    second_higest_offer = None

                # check if this offer is highest or outbid
                negotiated_offers = all_offers.filter(master_offer=negotiation_id)[0]
                if higest_offer and negotiated_offers.id == higest_offer.id:
                    # send high offer email
                    template_data = {"domain_id": domain_id, "slug": "loi_high_offer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "dashbaord_link": subdomain_url.replace("###", domain_name) + 'best-offers/'
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send outbid loi email to recent high bidder
                    if second_higest_offer:
                        template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": second_higest_offer.master_offer.user.first_name if second_higest_offer.master_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": second_higest_offer.offer_price,
                            "loi_link": loi_url
                        }
                        compose_email(to_email=[second_higest_offer.master_offer.user.email], template_data=template_data,
                                      extra_data=extra_data)
                else:
                    # check if this user was last higest bidder
                    last_high_offers = HighestBestNegotiatedOffers.objects \
                        .filter(status=1, is_declined=0, property=property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                        .exclude(id=current_neg_id) \
                        .order_by("-offer_price").first()

                    if last_high_offers.master_offer.user.id == master_offer.user_id:
                        # send high offer email
                        template_data = {"domain_id": domain_id, "slug": "loi_is_the_high_offer"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": higest_offer.master_offer.user.first_name if higest_offer.master_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": higest_offer.offer_price,
                            "dashbaord_link": subdomain_url.replace("###",domain_name) + 'asset-details/?property_id=' + str(property_id)
                        }
                        compose_email(to_email=[higest_offer.master_offer.user.email], template_data=template_data,
                                      extra_data=extra_data)
                    # send outbid email
                    template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": negotiated_offers.master_offer.user.first_name if negotiated_offers.master_offer.user.first_name is not None else "",
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[negotiated_offers.master_offer.user.email], template_data=template_data,
                                  extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerAcceptLoiView(APIView):
    """
    Seller accept loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id
            master_user_id = master_offer.user_id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 2:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            elif negotiated_offers.best_offer_is_accept == 1:
                return Response(response.parsejson("Offer already accepted.", "", status=403))

            # -----------------Update Offer--------------
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.display_status = 3
            negotiated_offers.save()

            try:
                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Highest & Best offer accepted"
                content = "Seller has accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=master_user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best offer accepted"
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)

                title = "Property Sold"
                content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=4)


                #===========Send Email===========================
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = negotiated_offers.user.first_name
                buyer_email = negotiated_offers.user.email
                # agent_email = property_detail.agent.email
                # agent_name = property_detail.agent.first_name
                # agent_phone = property_detail.agent.phone_no
                # accept_detail = negotiated_offers.best_offer_accept_by
                # accept_email = accept_detail.email if accept_detail.email is not None else ""
                # accept_name = accept_detail.first_name if accept_detail.first_name is not None else ""
                # accept_phone = accept_detail.phone_no if accept_detail.phone_no is not None else ""
                # web_url = settings.FRONT_BASE_URL
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                loi_url = subdomain_url.replace("###", domain_name)+"submit-loi/?property_id="+str(property_id)
                current_neg_id = negotiated_offers.id


                # if int(sale_by_type) == 7:
                #     domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                # else:
                #     domain_url = subdomain_url.replace("###", domain_name)+"my-offers"

                # check property uploads
                # image_url = web_url+'/static/admin/images/property-default-img.png'
                # upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                # if upload is not None:
                #     image = upload.upload.doc_file_name
                #     bucket_name = upload.upload.bucket_name
                #     image_url = settings.AWS_URL+bucket_name+'/'+image

                #================Email send property agent======================
                # if buyer_email.lower() != agent_email.lower():
                #     if int(sale_by_type) == 7:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                #     else:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                #     extra_data = {"user_name": agent_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                #     compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                
                #================Email send broker agent======================
                # if agent_email.lower() != broker_email.lower() and agent_email.lower() != buyer_email.lower():
                #     if int(sale_by_type) == 7:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                #     else:
                #         domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=traditional%20offer"
                #     extra_data = {"user_name": broker_name.title(), 'web_url': web_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'property_image': image_url, 'dashboard_link': domain_url, 'accepted_by': accepted_by, "domain_id": domain_id, "name": accept_name, "email": accept_email, "phone": phone_format(accept_phone)}
                #     compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)


                #================Send highest and outbid emails==========

                # get all last offer by buyers
                all_offers = NegotiatedOffers.objects\
                    .filter(status=1, property=property_id, best_offer_is_accept=1)\
                    .order_by('user_id', '-added_on')\
                    .distinct('user_id')\
                    .values_list('id', flat=True)
            
                all_offers = NegotiatedOffers.objects\
                    .filter(id__in=all_offers)\
                    .order_by('-added_on')
                
                
                # find max offer price
                max_offers = NegotiatedOffers.objects\
                            .filter(id__in=all_offers.values_list('id', flat=True))\
                            .order_by('-offer_price')
                try:
                    higest_offer = max_offers[0]
                except:
                    higest_offer = None
                
                try:
                    second_higest_offer = max_offers[1]
                except:
                    second_higest_offer = None

                
                
                # check if this offer is highest or outbid
                negotiated_offers = all_offers.filter(master_offer=negotiation_id)[0]
                if  higest_offer and negotiated_offers.id == higest_offer.id:
                    # send high offer email
                    template_data = {"domain_id": domain_id, "slug": "loi_high_offer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "dashbaord_link": subdomain_url.replace("###", domain_name)+'best-offers/'
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send outbid loi email to recent high bidder
                    if second_higest_offer:
                        template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": second_higest_offer.user.first_name if second_higest_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": second_higest_offer.offer_price,
                            "loi_link": loi_url
                        }
                        compose_email(to_email=[second_higest_offer.user.email], template_data=template_data, extra_data=extra_data)   
                else:
                    # check if this user was last higest bidder
                    last_high_offers = NegotiatedOffers.objects\
                        .filter(status=1, property=property_id, best_offer_is_accept=1)\
                        .exclude(id=current_neg_id)\
                        .order_by("-offer_price").last()

                    if last_high_offers.user_id == master_user_id:
                        # send high offer email
                        template_data = {"domain_id": domain_id, "slug": "loi_is_the_high_offer"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": higest_offer.user.first_name if higest_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": higest_offer.offer_price,
                            "dashbaord_link": subdomain_url.replace("###", domain_name)+'asset-details/?property_id='+property_id
                        }
                        compose_email(to_email=[higest_offer.user.email], template_data=template_data, extra_data=extra_data)

                    # send outbid email
                    template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": negotiated_offers.user.first_name if negotiated_offers.user.first_name is not None else "",
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[negotiated_offers.user.email], template_data=template_data, extra_data=extra_data)

            except:
                pass
            
            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedSellerAcceptLoiView(APIView):
    """
    Enhanced Seller accept loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (
                            Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(
                        network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(
                    Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (
                                Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id
            master_user_id = master_offer.user_id

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 2:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            elif negotiated_offers.best_offer_is_accept == 1:
                return Response(response.parsejson("Offer already accepted.", "", status=403))

            # -----------------Update Offer--------------
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.display_status = 3
            negotiated_offers.save()

            try:
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = negotiated_offers.master_offer.user.first_name
                buyer_email = negotiated_offers.master_offer.user.email
                agent_email = property_detail.agent.email
                # agent_name = property_detail.agent.first_name
                # agent_phone = property_detail.agent.phone_no
                # accept_detail = negotiated_offers.best_offer_accept_by
                # accept_email = accept_detail.email if accept_detail.email is not None else ""
                # accept_name = accept_detail.first_name if accept_detail.first_name is not None else ""
                # accept_phone = accept_detail.phone_no if accept_detail.phone_no is not None else ""
                # web_url = settings.FRONT_BASE_URL
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                loi_url = subdomain_url.replace("###", domain_name) + "submit-loi/?property_id=" + str(property_id)
                current_neg_id = negotiated_offers.id


                # ----------------Notifications-----------
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id
                title = "Highest & Best offer accepted"
                content = "Seller has accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=master_user_id, added_by=user_id,
                                 notification_for=1, property_id=property_id)

                if master_user_id != user_id:
                    content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)
                
                other_id = broker_detail.id if user_id == agent_id else agent_id
                content = "An offer has been accepted on! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=other_id, added_by=user_id, notification_for=2,
                                property_id=property_id, notification_type=6)

                # ================Send highest and outbid emails==========

                # get all last offer by buyers
                all_offers = HighestBestNegotiatedOffers.objects \
                    .filter(status=1, is_declined=0, property=property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                    .order_by('master_offer_id', '-added_on') \
                    .distinct('master_offer_id') \
                    .values_list('id', flat=True)

                all_offers = HighestBestNegotiatedOffers.objects \
                    .filter(id__in=all_offers) \
                    .order_by('-added_on')

                # find max offer price
                max_offers = HighestBestNegotiatedOffers.objects \
                    .filter(id__in=all_offers.values_list('id', flat=True)) \
                    .order_by('-offer_price')
                try:
                    higest_offer = max_offers[0]
                except:
                    higest_offer = None

                try:
                    second_higest_offer = max_offers[1]
                except:
                    second_higest_offer = None

                # check if this offer is highest or outbid
                negotiated_offers = all_offers.filter(master_offer=negotiation_id)[0]
                if higest_offer and negotiated_offers.id == higest_offer.id:
                    # send high offer email
                    template_data = {"domain_id": domain_id, "slug": "loi_high_offer"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": buyer_name.title(),
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "dashbaord_link": subdomain_url.replace("###", domain_name) + 'best-offers/'
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                    # send outbid loi email to recent high bidder
                    if second_higest_offer:
                        template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": second_higest_offer.master_offer.user.first_name if second_higest_offer.master_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": second_higest_offer.offer_price,
                            "loi_link": loi_url
                        }
                        compose_email(to_email=[second_higest_offer.master_offer.user.email], template_data=template_data,
                                      extra_data=extra_data)
                else:
                    # check if this user was last higest bidder
                    last_high_offers = HighestBestNegotiatedOffers.objects \
                        .filter(status=1, is_declined=0, property=property_id, best_offer_is_accept=1, master_offer__is_declined=0) \
                        .exclude(id=current_neg_id) \
                        .order_by("-offer_price").first()

                    if last_high_offers.master_offer.user.id == master_user_id:
                        # send high offer email
                        template_data = {"domain_id": domain_id, "slug": "loi_is_the_high_offer"}
                        extra_data = {
                            "domain_id": domain_id,
                            "user_name": higest_offer.master_offer.user.first_name if higest_offer.master_offer.user.first_name is not None else "",
                            "property_address": property_address,
                            "property_city": property_city,
                            "property_state": property_state,
                            "domain_name": domain_name.title(),
                            "owner_name": broker_name,
                            "owner_email": broker_email,
                            "owner_phone": phone_format(broker_phone),
                            "offer_amount": higest_offer.offer_price,
                            "dashbaord_link": subdomain_url.replace("###",
                                                                    domain_name) + 'asset-details/?property_id=' + str(property_id)
                        }
                        compose_email(to_email=[higest_offer.master_offer.user.email], template_data=template_data,
                                      extra_data=extra_data)

                    # send outbid email
                    template_data = {"domain_id": domain_id, "slug": "loi_outbid"}
                    extra_data = {
                        "domain_id": domain_id,
                        "user_name": negotiated_offers.master_offer.user.first_name if negotiated_offers.master_offer.user.first_name is not None else "",
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "domain_name": domain_name.title(),
                        "owner_name": broker_name,
                        "owner_email": broker_email,
                        "owner_phone": phone_format(broker_phone),
                        "offer_amount": negotiated_offers.offer_price,
                        "loi_link": loi_url
                    }
                    compose_email(to_email=[negotiated_offers.master_offer.user.email], template_data=template_data,
                                  extra_data=extra_data)

            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestSellerOfferListingView(APIView):
    """
    Best seller offer listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # master_offer = MasterOffer.objects.filter(Q(property=property_id) & Q(domain=domain_id))
            # master_offer = MasterOffer.objects.annotate(first_old_name=Window(expression=LastValue('negotiated_offers_master_offer__offer_price'), partition_by=[F('id'), ], order_by=F('negotiated_offers_master_offer__offer_price').desc())).filter(Q(property=property_id) & Q(domain=domain_id))
            master_offer = MasterOffer.objects.annotate(max_offer_price=Max('negotiated_offers_master_offer__offer_price')).filter(Q(property=property_id) & Q(domain=domain_id))
            master_offer = master_offer.order_by(F('max_offer_price').desc(nulls_last=True)).only("id")
            serializer = BestSellerOfferListingSerializer(master_offer, many=True)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestSellerOfferListingView(APIView):
    """
    Enhanced Best seller offer listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:

            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # master_offer = MasterOffer.objects.filter(Q(property=property_id) & Q(domain=domain_id))
            # master_offer = MasterOffer.objects.annotate(first_old_name=Window(expression=LastValue('negotiated_offers_master_offer__offer_price'), partition_by=[F('id'), ], order_by=F('negotiated_offers_master_offer__offer_price').desc())).filter(Q(property=property_id) & Q(domain=domain_id))
            # master_offer = MasterOffer.objects.annotate(max_offer_price=Max('highest_best_negotiated_offers_master_offer__offer_price')).filter(Q(highest_best_negotiated_offers_master_offer__id__gt=0) & Q(property=property_id) & Q(domain=domain_id))
            master_offer = MasterOffer.objects.annotate(max_offer_price=Max('highest_best_negotiated_offers_master_offer__added_on')).filter(Q(highest_best_negotiated_offers_master_offer__id__gt=0) & Q(property=property_id) & Q(domain=domain_id) & Q(status__in=[1, 18]))
            master_offer = master_offer.order_by("is_declined", F('max_offer_price').desc(nulls_last=True)).only("id")
            serializer = EnhancedBestSellerOfferListingSerializer(master_offer, many=True)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestSellerOfferDetailView(APIView):
    """
    Best seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "negotiated_id" in data and data['negotiated_id'] != "":
                negotiated_id = int(data['negotiated_id'])
            else:
                return Response(response.parsejson("negotiated_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            offers = MasterOffer.objects.filter(id=negotiated_id).last()
            serializer = BestSellerOfferDetailsSerializer(offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestSellerOfferDetailView(APIView):
    """
    Enhanced Best seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "negotiated_id" in data and data['negotiated_id'] != "":
                negotiated_id = int(data['negotiated_id'])
            else:
                return Response(response.parsejson("negotiated_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=2) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__is_agent=1) & Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            offers = MasterOffer.objects.filter(id=negotiated_id).last()
            serializer = EnhancedBestSellerOfferDetailsSerializer(offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestBuyerOfferDetailView(APIView):
    """
    Best buyer offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(Q(user=user_id) & Q(master_offer__property=property_id) & Q(master_offer__user=user_id) & Q(master_offer__domain=domain_id) & Q(status=1)).last()
            serializer = BestBuyerOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestBuyerOfferDetailView(APIView):
    """
    Enhanced Best buyer offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(user=user_id) & Q(master_offer__property=property_id) & Q(master_offer__user=user_id) & Q(master_offer__domain=domain_id) & Q(status=1)).last()
            serializer = EnhancedBestBuyerOfferDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestCurrentOfferView(APIView):
    """
    Best current offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = NegotiatedOffers.objects.filter(Q(master_offer__property=property_id) & Q(master_offer__domain=domain_id) & Q(best_offer_is_accept=1) & Q(status=1)).order_by("offer_price").last()
            all_data = {}
            if negotiated_offers is not None:
                serializer = BestCurrentOfferSerializer(negotiated_offers)
                all_data['data'] = serializer.data
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestCurrentOfferView(APIView):
    """
    Enhanced Best current offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(master_offer__property=property_id) & Q(master_offer__domain=domain_id) & Q(master_offer__is_declined=0) & Q(best_offer_is_accept=1) & Q(status=1) & Q(is_declined=0)).order_by("offer_price").last()

            all_data = {}
            if negotiated_offers is not None:
                serializer = EnhancedBestCurrentOfferSerializer(negotiated_offers)
                all_data['data'] = serializer.data
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BuyerAcceptBestOfferView(APIView):
    """
    Buyer accept best offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[4, 7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 1:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.save()
            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 1
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()

            try:
                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Highest & Best offer accepted"
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best offer accepted"
                content = "Buyer accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                title = "Property sold"
                content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                # ===========Send Email===========================
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = user.first_name
                buyer_email = user.email
                buyer_phone = user.phone_no
                agent_email = property_listing.agent.email
                agent_name = property_listing.agent.first_name
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_listing.address_one
                property_city = property_listing.city
                property_state = property_listing.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name

                #================Email send buyer==========================
                template_data = {"domain_id": domain_id, "slug": "loi_accepted_buyer"}
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                contact_person =  'Broker' if property_listing.agent.id == negotiated_offers.user.id else 'Agent'
                contact_person_detail = broker_detail if property_listing.agent.id == negotiated_offers.user.id else property_listing.agent
                extra_data = {
                    "user_name": buyer_name.title(),
                    'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'contact_person':contact_person,
                    'contact_person_name': contact_person_detail.first_name,
                    'contact_person_phone': contact_person_detail.email,
                    'contact_person_email': phone_format(contact_person_detail.phone_no),
                    "domain_id": domain_id,
                    "owner_name": broker_name,
                    "owner_email": broker_email,
                    "owner_phone": phone_format(broker_phone),
                    "domain_name":domain_name
                }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)


                template_data = {"domain_id": domain_id, "slug": "accept_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address, 
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    'accepted_by': 'buyer',
                    "domain_id": domain_id,
                    "name": buyer_name,
                    "email": buyer_email,
                    "phone": phone_format(buyer_phone)
                }

                if agent_email.lower() != buyer_email.lower():
                    #================Email send property agent======================
                    extra_data["user_name"] = agent_name.title()
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    #================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    extra_data["user_name"] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SellerAcceptBestOfferView(APIView):
    """
    Seller accept best offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            elif master_offer.accepted_by is not None:
                return Response(response.parsejson("Offer already accept.", "", status=403))
            master_id = master_offer.id
            master_user_id = master_offer.user_id

            negotiated_offers = NegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 2:
                return Response(response.parsejson("You can't accept offer.", "", status=403))

            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.save()
            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 2
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()

            try:
                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Highest & Best offer accepted"
                content = "Seller has accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=master_user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Highest & Best offer accepted."
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                title = "Property Sold"
                content = "Your Property has been Sold! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
                
                #===========Send Email===========================
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                agent_email = property_listing.agent.email
                agent_name = property_listing.agent.first_name
                accept_email = user.email if user.email is not None else ""
                accept_name = user.first_name if user.first_name is not None else ""
                accept_phone = user.phone_no if user.phone_no is not None else ""
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_listing.address_one
                property_city = property_listing.city
                property_state = property_listing.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                accepted_by = 'broker' if broker_detail.id == property_listing.agent.id else 'agent'

                #================Email send buyer==========================
                template_data = {"domain_id": domain_id, "slug": "loi_accepted_seller"}
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                contact_person =  'Broker' if property_listing.agent.id == negotiated_offers.user.id else 'Agent'
                contact_person_detail = broker_detail if property_listing.agent.id == negotiated_offers.user.id else property_listing.agent
                extra_data = {
                    "user_name": buyer_name.title(),
                    'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'accepted_by': accepted_by,
                    'contact_person':contact_person,
                    'contact_person_name': contact_person_detail.first_name,
                    'contact_person_phone': contact_person_detail.email,
                    'contact_person_email': phone_format(contact_person_detail.phone_no),
                    "domain_id": domain_id,
                    "owner_name": broker_name,
                    "owner_email": broker_email,
                    "owner_phone": phone_format(broker_phone),
                    "domain_name":domain_name
                }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                template_data = {"domain_id": domain_id, "slug": "accept_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    'accepted_by': accepted_by,
                    "domain_id": domain_id,
                    "name": accept_name,
                    "email": accept_email,
                    "phone": phone_format(accept_phone)
                }
                if buyer_email.lower() != agent_email.lower():
                    #================Email send property agent======================
                    extra_data["user_name"] = agent_name.title()
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    #================Email send broker======================
                if agent_email.lower() != broker_email.lower() and agent_email.lower() != buyer_email.lower():
                    extra_data["user_name"] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            
            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBuyerAcceptBestOfferView(APIView):
    """
    Enhanced Buyer accept best offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[4, 7], is_approved=1, status=1).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))

            master_id = master_offer.id

            master_offer_count = MasterOffer.objects.filter(property=property_id, accepted_by__isnull=False).count()
            if master_offer_count:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_id, is_declined=0, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 1:
                return Response(response.parsejson("You can't accept offer.", "", status=403))
            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.save()
            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 1
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()

            try:
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_name = user.first_name
                buyer_email = user.email
                buyer_phone = user.phone_no
                agent_email = property_listing.agent.email
                agent_name = property_listing.agent.first_name
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_listing.address_one
                property_city = property_listing.city
                property_state = property_listing.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name

                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Congratulations! You won a property"
                content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=1, property_id=property_id)

                title = "Congratulations! Property Sold"
                if user_id != agent_id:
                    content = "Buyer accepted your offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)

                if agent_id != broker_detail.id:
                    content = "Buyer accepted an offer on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)


                #================Email send buyer==========================
                template_data = {"domain_id": domain_id, "slug": "loi_accepted_buyer"}
                domain_url = subdomain_url.replace("###", domain_name)+"best-offers"
                contact_person =  'Broker' if property_listing.agent.id == negotiated_offers.user.id else 'Agent'
                contact_person_detail = broker_detail if property_listing.agent.id == negotiated_offers.user.id else property_listing.agent
                extra_data = {
                    "user_name": buyer_name.title(),
                    'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'contact_person':contact_person,
                    'contact_person_name': contact_person_detail.first_name,
                    'contact_person_phone': contact_person_detail.email,
                    'contact_person_email': phone_format(contact_person_detail.phone_no),
                    "domain_id": domain_id,
                    "owner_name": broker_name,
                    "owner_email": broker_email,
                    "owner_phone": phone_format(broker_phone),
                    "domain_name":domain_name
                }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)


                template_data = {"domain_id": domain_id, "slug": "accept_offer"}
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    'accepted_by': 'buyer',
                    "domain_id": domain_id,
                    "name": buyer_name,
                    "email": buyer_email,
                    "phone": phone_format(buyer_phone)
                }

                if agent_email.lower() != buyer_email.lower():
                    #================Email send property agent======================
                    extra_data["user_name"] = agent_name.title()
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    #================Email send broker agent======================
                if agent_email.lower() != broker_email.lower() and broker_email.lower() != buyer_email.lower():
                    extra_data["user_name"] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedSellerAcceptBestOfferView(APIView):
    """
    Enhanced Seller accept best offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (
                            Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(
                        network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(
                    Q(id=property_id) & Q(sale_by_type__in=[4, 7]) & Q(status=1) & Q(domain=domain_id) & (
                                Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            master_id = master_offer.id
            master_user_id = master_offer.user_id

            master_offer_count = MasterOffer.objects.filter(property=property_id, accepted_by__isnull=False).count()
            if master_offer_count:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_id, is_declined=0, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for accept.", "", status=403))
            elif negotiated_offers.offer_by == 2:
                return Response(response.parsejson("You can't accept offer.", "", status=403))

            negotiated_offers.best_offer_is_accept = 1
            negotiated_offers.best_offer_accept_by_id = user_id
            negotiated_offers.save()
            # --------------Update Master offer----------
            master_offer.accepted_by_id = user_id
            master_offer.accepted_amount = negotiated_offers.offer_price
            master_offer.accepted_date = datetime.datetime.now()
            master_offer.final_by = 2
            master_offer.status_id = 18
            master_offer.save()
            # --------------Update Property Listing----------
            property_listing.status_id = 9
            property_listing.closing_status_id = 9
            property_listing.sold_price = negotiated_offers.offer_price
            property_listing.winner_id = user_id
            property_listing.date_sold = datetime.datetime.now()
            property_listing.save()
            # --------------Update Property Auction----------
            property_auction = PropertyAuction.objects.filter(domain=domain_id, property=property_id).first()
            property_auction.status_id = 9
            property_auction.save()

            try:
                broker_detail = Users.objects.get(site_id=domain_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                broker_phone = broker_detail.phone_no
                buyer_datail = master_offer.user
                buyer_name = buyer_datail.first_name
                buyer_email = buyer_datail.email
                agent_email = property_listing.agent.email
                agent_name = property_listing.agent.first_name
                accept_email = user.email if user.email is not None else ""
                accept_name = user.first_name if user.first_name is not None else ""
                accept_phone = user.phone_no if user.phone_no is not None else ""
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url + '/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL + bucket_name + '/' + image
                property_address = property_listing.address_one
                property_city = property_listing.city
                property_state = property_listing.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                accepted_by = 'broker' if broker_detail.id == user_id else 'agent'

                # ----------------Notifications-----------
                prop_name = property_listing.address_one if property_listing.address_one else property_listing.id
                title = "Congratulations! You won a property"
                content = "Seller has accepted your offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=master_user_id, added_by=user_id,
                                 notification_for=1, property_id=property_id)
                
                title = "Congratulations! Property Sold"
                if master_user_id != agent_id:
                    content = "You accepted an offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=agent_id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)
                
                if agent_id != broker_detail.id:
                    content = "Seller has accepted an offer on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=broker_detail.id, added_by=user_id, notification_for=2,
                                    property_id=property_id, notification_type=6)

                # ================Email send buyer==========================
                template_data = {"domain_id": domain_id, "slug": "loi_accepted_seller"}
                domain_url = subdomain_url.replace("###", domain_name) + "best-offers"
                contact_person = 'Broker' if broker_detail.id == user_id else 'Agent'
                contact_person_detail = broker_detail if broker_detail.id == user_id  else property_listing.agent
                extra_data = {
                    "user_name": buyer_name.title(),
                    'offer_amount': '$' + number_format(negotiated_offers.offer_price),
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'accepted_by': accepted_by,
                    'contact_person': contact_person,
                    'contact_person_name': contact_person_detail.first_name,
                    'contact_person_phone': contact_person_detail.email,
                    'contact_person_email': phone_format(contact_person_detail.phone_no),
                    "domain_id": domain_id,
                    "owner_name": broker_name,
                    "owner_email": broker_email,
                    "owner_phone": phone_format(broker_phone),
                    "domain_name": domain_name
                }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                template_data = {"domain_id": domain_id, "slug": "accept_offer"}
                domain_url = subdomain_url.replace("###", domain_name) + "admin/listing/?auction_type=highest%20offer"
                extra_data = {
                    'web_url': web_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'property_image': image_url,
                    'dashboard_link': domain_url,
                    'accepted_by': accepted_by,
                    "domain_id": domain_id,
                    "name": accept_name,
                    "email": accept_email,
                    "phone": phone_format(accept_phone)
                }
                if buyer_email.lower() != agent_email.lower():
                    # ================Email send property agent======================
                    extra_data["user_name"] = agent_name.title()
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                    # ================Email send broker======================
                if agent_email.lower() != broker_email.lower() and agent_email.lower() != buyer_email.lower():
                    extra_data["user_name"] = broker_name.title()
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)

            except:
                pass

            return Response(response.parsejson("Offer accepted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EnhancedBestSellerCounterOfferView(APIView):
    """
    Enhanced Best Seller Counter Offer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=domain_id) | (Q(network_user__domain=domain_id) & Q(network_user__is_agent=1) & Q(network_user__status=1)))).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(Q(id=property_id) & Q(sale_by_type__in=[7]) & Q(status=1) & Q(domain=domain_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id)) & Q(is_approved=1)).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
                agent_id = property_listing.agent_id
                sale_by_type = property_listing.sale_by_type_id
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "offer_price" in data and data['offer_price'] != "":
                offer_price = data['offer_price']
            else:
                return Response(response.parsejson("offer_price is required", "", status=403))

            comment = None
            if "offer_comment" in data and data['offer_comment'] != "":
                comment = data['offer_comment']

            negotiation_id = None
            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])

            if "earnest_money_deposit" in data and data['earnest_money_deposit'] != "":
                earnest_money_deposit = data['earnest_money_deposit']
            else:
                return Response(response.parsejson("earnest_money_deposit is required", "", status=403))

            if "down_payment" in data and data['down_payment'] != "":
                down_payment = data['down_payment']
            else:
                return Response(response.parsejson("down_payment is required", "", status=403))

            if "due_diligence_period" in data and data['due_diligence_period'] != "":
                due_diligence_period = int(data['due_diligence_period'])
            else:
                return Response(response.parsejson("due_diligence_period is required", "", status=403))

            if "closing_period" in data and data['closing_period'] != "":
                closing_period = int(data['closing_period'])
                if property_listing.escrow_period is not None and closing_period > property_listing.escrow_period:
                    return Response(response.parsejson("closing_period should be less or equal to " + str(property_listing.escrow_period), "", status=403))
            else:
                return Response(response.parsejson("closing_period is required", "", status=403))

            if "financing" in data and data['financing'] != "":
                financing = int(data['financing'])
            else:
                return Response(response.parsejson("financing is required", "", status=403))

            if "offer_contingent" in data and data['offer_contingent'] != "":
                offer_contingent = int(data['offer_contingent'])
            else:
                return Response(response.parsejson("offer_contingent is required", "", status=403))

            if "sale_contingency" in data and data['sale_contingency'] != "":
                sale_contingency = int(data['sale_contingency'])
            else:
                return Response(response.parsejson("sale_contingency is required", "", status=403))

            if "appraisal_contingent" in data and data['appraisal_contingent'] != "":
                appraisal_contingent = int(data['appraisal_contingent'])
            else:
                return Response(response.parsejson("appraisal_contingent is required", "", status=403))

            if "closing_cost" in data and data['closing_cost'] != "":
                closing_cost = int(data['closing_cost'])
            else:
                return Response(response.parsejson("closing_cost is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id, status=1, is_canceled=0, is_declined=0).last()
            if master_offer is None:
                return Response(response.parsejson("Offer not found.", "", status=403))
            master_id = master_offer.id

            max_dt = timezone.now()
            # property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt, end_date__gte=max_dt).first()
            property_auction = PropertyAuction.objects.filter(property=property_id, start_date__lte=max_dt).first()
            if property_auction is None:
                return Response(response.parsejson("Offer not started yet., end date.", "", status=403))
            if property_auction.status_id != 1:
                return Response(response.parsejson("Offer not active.", "", status=403))

            master_offer_count = MasterOffer.objects.filter(property=property_id, accepted_by__isnull=False).count()
            if master_offer_count:
                return Response(response.parsejson("Offer already accept.", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(master_offer=master_id, status=1).last()
            if negotiated_offers is None:
                return Response(response.parsejson("No offer for counter.", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers()
            negotiated_offers.domain_id = domain_id
            negotiated_offers.property_id = property_id
            negotiated_offers.master_offer_id = master_id
            negotiated_offers.user_id = user_id
            negotiated_offers.offer_by = 2
            negotiated_offers.display_status = 2
            negotiated_offers.offer_price = offer_price
            negotiated_offers.comments = comment
            negotiated_offers.status_id = 1
            negotiated_offers.earnest_money_deposit = earnest_money_deposit
            negotiated_offers.down_payment = down_payment
            negotiated_offers.due_diligence_period = due_diligence_period
            negotiated_offers.closing_period = closing_period
            negotiated_offers.financing = financing
            negotiated_offers.offer_contingent = offer_contingent
            negotiated_offers.sale_contingency = sale_contingency
            negotiated_offers.appraisal_contingent = appraisal_contingent
            negotiated_offers.closing_cost = closing_cost
            negotiated_offers.save()

            try:
                #==================Email send=============================
                property_detail = negotiated_offers.property
                broker_detail = Users.objects.get(site_id=domain_id)
                buyer_name = master_offer.user.first_name
                buyer_email = master_offer.user.email
                buyer_phone = master_offer.user.phone_no
                user_counter_name = negotiated_offers.user.first_name if negotiated_offers.user is not None else ""
                user_counter_email = negotiated_offers.user.email if negotiated_offers.user.email is not None else ""
                user_counter_phone = negotiated_offers.user.phone_no if negotiated_offers.user.phone_no is not None else ""
                if int(negotiated_offers.user.user_type.id) ==  2 and negotiated_offers.user.site_id is None:
                    #user type agent
                    counter_by = 'agent'
                    other_user_detail = broker_detail
                else:
                    #user type broker
                    counter_by = 'broker'
                    other_user_detail = Users.objects.get(id=property_detail.agent_id)
                
                other_user_name = other_user_detail.first_name if other_user_detail.first_name is not None else ""
                other_user_email = other_user_detail.email if other_user_detail.email is not None else ""
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                closing_period_text = {1: "1-30 Days", 2: "30-45 Days", 3: "45-60 Days", 4: "61+ Days"}

                 # ----------------Notifications-----------
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id
                title = "Highest & Best Counter offer"
                # to agent/broker
                content = "You made a Counter-Offer! <span>[" + prop_name + "]</span>"
                add_notification(domain_id, title, content, user_id=user_id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
                
                # to other agent/broker
                if user_id != other_user_detail.id:
                    content = "New counter offer made by "+ counter_by +" on! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=other_user_detail.id, added_by=user_id, notification_for=2, property_id=property_id, notification_type=6)
                
                # notification to buyer
                if user_id != master_offer.user_id:
                    content = "You’ve Received a Counter-Offer! <span>[" + prop_name + "]</span>"
                    add_notification(domain_id, title, content, user_id=master_offer.user_id, added_by=user_id, notification_for=1, property_id=property_id)
                

                # send email to buyer
                domain_url = subdomain_url.replace("###",
                                                    domain_name) + "admin/listing/?auction_type=highest%20offer"
                template_data = {"domain_id": domain_id, "slug": "high_and_best_counter_offer_sent"}

                extra_data = {
                    "user_name": user_counter_name,
                    "name": buyer_name,
                    "email": buyer_email,
                    "phone": phone_format(buyer_phone),
                    "offer_price": number_format(offer_price),
                    "earnest_money_deposit": "$" + number_format(earnest_money_deposit) if property_detail.earnest_deposit_type == 1 else str(earnest_money_deposit) + "%",
                    "down_payment": number_format(down_payment),
                    "closing_date": closing_period_text[closing_period],
                    "message": comment,
                    "property_address": property_address,
                    "property_city": property_city,
                    "property_state": property_state,
                    "property_image": image_url,
                    "dashboard_link": domain_url,
                    "domain_id": domain_id
                }
                compose_email(to_email=[negotiated_offers.user.email], template_data=template_data, extra_data=extra_data)

                if negotiated_offers.user.id != other_user_detail.id:
                    extra_data['user_name'] = other_user_name
                    compose_email(to_email=[other_user_email], template_data=template_data, extra_data=extra_data)

                if negotiated_offers.user.id != master_offer.user.id:
                    # send email to agent and broker
                    template_data = {"domain_id": domain_id, "slug": "high_and_best_counter_offer_received"}
                    domain_url = subdomain_url.replace("###", domain_name) + "best-offers"
                    extra_data = {
                        "user_name": buyer_name,
                        "property_address": property_address,
                        "property_city": property_city,
                        "property_state": property_state,
                        "property_image": image_url,
                        "dashboard_link": domain_url,
                        "offer_price": number_format(offer_price),
                        "earnest_money_deposit": "$" + number_format(earnest_money_deposit) if property_detail.earnest_deposit_type == 1 else str(earnest_money_deposit) + "%",
                        "down_payment": number_format(down_payment),
                        "closing_date": closing_period_text[closing_period],
                        "message": comment,
                        "counter_by": counter_by,
                        "domain_id": domain_id,
                        "name": user_counter_name,
                        "email": user_counter_email,
                        "phone": phone_format(user_counter_phone)
                    }
                    compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            
            except:
                pass

            return Response(response.parsejson("Counter offer successfully submitted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BestOfferHistoryDetailView(APIView):
    """
    Best offer history detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "best_offers_id" in data and data['best_offers_id'] != "":
                best_offers_id = int(data['best_offers_id'])
            else:
                return Response(response.parsejson("best_offers_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(id=best_offers_id) & Q(property=property_id) & Q(domain=domain_id)).last()
            serializer = BestOfferHistoryDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminBestSellerOfferListingView(APIView):
    """
    Super Admin Best seller offer listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user = Users.objects.filter(Q(id=data['user_id']) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            master_offer = MasterOffer.objects.annotate(max_offer_price=Max('highest_best_negotiated_offers_master_offer__added_on')).filter(Q(highest_best_negotiated_offers_master_offer__id__gt=0) & Q(property=property_id) & Q(status__in=[1, 18]))
            master_offer = master_offer.order_by("is_declined", F('max_offer_price').desc(nulls_last=True)).only("id")
            serializer = SuperAdminSellerOfferListingSerializer(master_offer, many=True)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminBestSellerOfferDetailView(APIView):
    """
    Super Admin Best seller offer detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "negotiated_id" in data and data['negotiated_id'] != "":
                negotiated_id = int(data['negotiated_id'])
            else:
                return Response(response.parsejson("negotiated_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            offers = MasterOffer.objects.filter(id=negotiated_id).last()
            serializer = SuperAdminBestSellerOfferDetailsSerializer(offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminBestOfferHistoryDetailView(APIView):
    """
    Super Admin Best offer history detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "best_offers_id" in data and data['best_offers_id'] != "":
                best_offers_id = int(data['best_offers_id'])
            else:
                return Response(response.parsejson("best_offers_id is required", "", status=403))

            negotiated_offers = HighestBestNegotiatedOffers.objects.filter(Q(id=best_offers_id) & Q(property=property_id)).last()
            serializer = SuperAdminBestOfferHistoryDetailSerializer(negotiated_offers)
            all_data = {
                'data': serializer.data
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminGetLoiView(APIView):
    """
    Super Admin Get loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            # if "user" in data and data['user'] != "":
            #     user_id = int(data['user'])
            #     user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
            #     if user is None:
            #         return Response(response.parsejson("User not exist.", "", status=403))
            # else:
            #     return Response(response.parsejson("user is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            master_offer = MasterOffer.objects.filter(property=property_id, user=user_id).first()
            serializer = SuperAdminGetLoiSerializer(master_offer)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminSendLoiView(APIView):
    """
    Super Admin Send Loi
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_listing = PropertyListing.objects.filter(id=property_id, sale_by_type__in=[7]).first()
                if property_listing is None:
                    return Response(response.parsejson("Listing not found.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required", "", status=403))

            if "negotiation_id" in data and data['negotiation_id'] != "":
                negotiation_id = int(data['negotiation_id'])
            else:
                return Response(response.parsejson("negotiation_id is required", "", status=403))

            master_offer = MasterOffer.objects.filter(id=negotiation_id).first()
            domain = master_offer.domain_id
            domain_name = master_offer.domain.domain_name
            serializer = SendLoiSerializer(master_offer)
            notification_template = NotificationTemplate.objects.filter(Q(site=domain) & Q(event__slug='offer_loi') & Q(status=1)).first()
            if notification_template is None:
                notification_template = NotificationTemplate.objects.filter(Q(event__slug='offer_loi') & Q(site__isnull=True) & Q(status=1)).first()
            extra = {"domain_id": domain, "message": message, "domain_name": domain_name}
            send_custom_email(to_email=[email], template_id=notification_template.id, subject="Offer Document", extra=extra, attachment=serializer.data)
            return Response(response.parsejson("Send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendDutchEmailView(APIView):
    """
    Send dutch email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "bid_amount" in data and data['bid_amount'] != "":
                bid_amount = int(data['bid_amount'])
            else:
                return Response(response.parsejson("bid_amount is required", "", status=403))

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(property_id)

            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            template_data = {"domain_id": domain_id, "slug": "dutch_winner"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendSealedEmailView(APIView):
    """
    Send sealed email
    """

    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "bid_amount" in data and data['bid_amount'] != "":
                bid_amount = int(data['bid_amount'])
            else:
                return Response(response.parsejson("bid_amount is required", "", status=403))

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(property_id)

            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            template_data = {"domain_id": domain_id, "slug": "sealed_bid"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendEnglishEmailView(APIView):
    """
    Send english email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            bid_amount = data['bid_amount'] if data['bid_amount'] is not None else 0

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(property_id)

            # send email to buyer
            step_data = InsiderAuctionStepWinner.objects.filter(domain=domain_id, property=property_id, insider_auction_step=2, status=1).first()
            starting_price = 0
            if step_data is not None:
                starting_price = int(step_data.amount) + int(auction_data.bid_increments)

            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(starting_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            template_data = {"domain_id": domain_id, "slug": "bid_confirmation"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

            extra_data['buyer_name'] = user.first_name + ' ' + user.last_name
            extra_data['buyer_email'] = user.email
            extra_data['buyer_phone'] = phone_format(user.phone_no)
            extra_data['dashboard_link'] = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "admin/listing/"

            if user.id != auction_data.property.agent.id:
                # send email to agent
                extra_data['dashboard_link'] = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "admin/listing/?auction_type=insider%20auction"
                extra_data['user_name'] = auction_data.property.agent.first_name.title() + ' ' + auction_data.property.agent.last_name.title()
                template_data = {"domain_id": domain_id, "slug": "bid_confirmation_seller"}
                compose_email(to_email=[auction_data.property.agent.email], template_data=template_data, extra_data=extra_data)

            if broker_detail.id != auction_data.property.agent.id and user_id != broker_detail.id:
                # send email to broker
                extra_data['dashboard_link'] = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "admin/listing/?auction_type=insider%20auction"
                extra_data['user_name'] = broker_detail.first_name.title() + ' ' + broker_detail.last_name.title()
                template_data = {"domain_id": domain_id, "slug": "bid_confirmation_seller"}
                compose_email(to_email=[broker_detail.email], template_data=template_data, extra_data=extra_data)

            prop_name = auction_data.property.address_one if auction_data.property.address_one else auction_data.property.id
            try:
                # send email to outbidder
                outbidder = Bid.objects.filter(bid_type__in=[2, 3], is_canceled=0, property=property_id, auction_type=2, insider_auction_step=3).exclude(user_id=user_id).order_by('-id').first()
                if outbidder is None:
                    outbidder = Bid.objects.filter(bid_type__in=[2, 3], is_canceled=0, property=property_id, auction_type=2, insider_auction_step=1).exclude(user_id=user_id).order_by('-id').first()
                # outbidder_id = outbidder[0].user_id
                if outbidder is not None and outbidder.user.id and user_id != outbidder.user.id:
                    extra_data['dashboard_link'] = domain_url
                    extra_data['user_name'] = outbidder.user.first_name.title() + ' ' + outbidder.user.last_name.title()
                    extra_data['bid_amount'] = number_format(outbidder.bid_amount)

                    template_data = {"domain_id": domain_id, "slug": "outbid"}
                    compose_email(to_email=[outbidder.user.email], template_data=template_data, extra_data=extra_data)

                    #  add notfification to buyer(outbidder)
                    content = "You have been outbid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "OutBid Alert",
                        content,
                        user_id=outbidder.user.id,
                        added_by=outbidder.user.id,
                        notification_for=1,
                        property_id=property_id
                    )
            except:
                pass

            try:
                #  add notfification to buyer
                content = "Your bid has been confirmed! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain_id,
                    "Bid Confirmation",
                    content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    property_id=property_id
                )
                if user_id != auction_data.property.agent.id:
                    content = "You have received one new bid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "Bid Received",
                        content,
                        user_id=auction_data.property.agent.id,
                        added_by=auction_data.property.agent.id,
                        notification_for=2,
                        property_id=property_id
                    )
                if broker_detail.id != auction_data.property.agent.id and user_id != broker_detail.id:
                    content = "You have received one new bid! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain_id,
                        "Bid Received",
                        content,
                        user_id=broker_detail.id,
                        added_by=broker_detail.id,
                        notification_for=2,
                        property_id=property_id
                    )

            except:
                pass

            # message = "Property="+str(property_id)+" Domain id="+str(domain_id)+" User Id="+str(user_id)+" Bid amount="+str(bid_amount)
            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class InsiderBidderView(APIView):
    """
    Insider bidder
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

            if "step" in data and data['step'] != "":
                step = data['step']
            else:
                return Response(response.parsejson("step is required", "", status=403))

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=domain_id, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain_id, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            property_address = {}
            property_image = {}
            property_listing = PropertyListing.objects.filter(id=property_id).first()
            if property_listing is not None:
                property_address['address_one'] = property_listing.address_one
                property_address['city'] = property_listing.city
                property_address['state'] = property_listing.state.state_name
                property_address['postal_code'] = property_listing.postal_code
                image = property_listing.property_uploads_property.filter(upload_type=1).first()
                if image is not None:
                    property_image = {"image": image.upload.doc_file_name, "bucket_name": image.upload.bucket_name}

            bid = Bid.objects.filter(domain=domain_id, property=property_id, auction_type=2, is_canceled=0)
            if step == "dutch":
                bid = bid.filter(insider_auction_step=1)
            elif step == "sealed":
                bid = bid.filter(insider_auction_step=2)
            elif step == "english":
                bid = bid.filter(insider_auction_step=3)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     bid = bid.filter(Q(id=search))
                bid = bid.annotate(user_name=Concat('user__first_name', V(', '), 'user__last_name', output_field=CharField())).filter(Q(user_name__icontains=search) | Q(user__user_type__user_type__icontains=search) | Q(user__email__icontains=search) | Q(user__phone_no__icontains=search) | Q(ip_address__icontains=search) | Q(auction__start_price__icontains=search))
            total = bid.count()
            bid = bid.order_by("-id").only("id")[offset: limit]
            if step == "dutch":
                serializer = DutchInsiderBidderSerializer(bid, many=True)
            elif step == "sealed":
                serializer = SealedInsiderBidderSerializer(bid, many=True)
            elif step == "english":
                serializer = EnglishInsiderBidderSerializer(bid, many=True)
            all_data = {
                "property_address": property_address,
                "property_image": property_image,
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
        

class SendEnglishEndEmailView(APIView):
    """
    Send english end email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "bid_amount" in data and data['bid_amount'] != "":
                bid_amount = int(data['bid_amount'])
            else:
                return Response(response.parsejson("bid_amount is required", "", status=403))

            insider_auction_step_winner = InsiderAuctionStepWinner.objects.filter(domain=domain_id, property=property_id, insider_auction_step__in=[1, 2]).exclude(user=user_id).first()
            lost_user_id = None
            if insider_auction_step_winner is not None and insider_auction_step_winner.user_id != user_id:
                lost_user_id = insider_auction_step_winner.user_id

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(
                property_id)

            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            # ------English Winner User Email------
            template_data = {"domain_id": domain_id, "slug": "insider_english_winner"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

            # ------English Lost User Email------
            if lost_user_id is not None:
                user = Users.objects.get(id=lost_user_id)
                extra_data["user_name"] = user.first_name + ' ' + user.last_name
                template_data = {"domain_id": domain_id, "slug": "insider_english_auction_lost"}
                compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendSealedEndEmailView(APIView):
    """
    Send Sealed end email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "bid_amount" in data and data['bid_amount'] != "":
                bid_amount = int(data['bid_amount'])
            else:
                return Response(response.parsejson("bid_amount is required", "", status=403))

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(
                property_id)

            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            # ------Sealed Winner User Email------
            template_data = {"domain_id": domain_id, "slug": "sealed_bid_winner"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

            # ------Sealed Lost User Email------
            all_lost_user = Bid.objects.values("user", "user__first_name", "user__last_name", "user__email").annotate(dcount=Count('user')).filter(property=property_id, auction_type=2, insider_auction_step=2, is_canceled=0).exclude(user=user_id)
            for i in all_lost_user:
                extra_data['user_name'] = i['user__first_name'] + ' ' + i['user__last_name']
                template_data = {"domain_id": domain_id, "slug": "insider_english_auction_lost"}
                compose_email(to_email=[i['user__email']], template_data=template_data, extra_data=extra_data)

            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class InlineBiddingListingView(APIView):
    """
    Bid registration listing
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).exclude(user_type=3).first()
                # user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.filter(Q(domain=site_id) & Q(user=user_id) & Q(property__sale_by_type=2)).exclude(Q(status__in=[2, 5]) | Q(property__status=5))
            # -------Filter-------
            if "asset_type" in data and data['asset_type'] != "":
                asset_type = int(data['asset_type'])
                bid_registration = bid_registration.filter(property__property_asset=asset_type)

            if "filter_data" in data and data['filter_data'] != "":
                if int(data['filter_data']) == 1:  # ----------For pending------------
                    bid_registration = bid_registration.filter(is_approved=1)
                elif int(data['filter_data']) == 2:  # ----------For approved------------
                    bid_registration = bid_registration.filter(is_approved=2)
                elif int(data['filter_data']) == 3:  # ----------For rejected------------
                    bid_registration = bid_registration.filter(is_approved=3)
                elif int(data['filter_data']) == 4:  # ----------For reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=1)
                elif int(data['filter_data']) == 5:  # ----------For not reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=0)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    bid_registration = bid_registration.filter(Q(id=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search))
                else:
                    bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('view_bid_registration_address_registration__first_name', V(' '), 'view_bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(view_bid_registration_address_registration__first_name__icontains=search) | Q(view_bid_registration_address_registration__last_name__icontains=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search) | Q(view_bid_registration_address_registration__email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(view_bid_registration_address_registration__city__icontains=search))
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = InlineBiddingListingSerializer(bid_registration, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminInlineBiddingListingView(APIView):
    """
    Insider bidder
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

            if "step" in data and data['step'] != "":
                step = data['step']
            else:
                return Response(response.parsejson("step is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))
            property_address = {}
            property_image = {}
            property_listing = PropertyListing.objects.filter(id=property_id).first()
            if property_listing is not None:
                property_address['address_one'] = property_listing.address_one
                property_address['city'] = property_listing.city
                property_address['state'] = property_listing.state.state_name
                property_address['postal_code'] = property_listing.postal_code
                image = property_listing.property_uploads_property.filter(upload_type=1).first()
                if image is not None:
                    property_image = {"image": image.upload.doc_file_name, "bucket_name": image.upload.bucket_name}

            bid = Bid.objects.filter(property=property_id, auction_type=2, is_canceled=0)
            if step == "dutch":
                bid = bid.filter(insider_auction_step=1)
            elif step == "sealed":
                bid = bid.filter(insider_auction_step=2)
            elif step == "english":
                bid = bid.filter(insider_auction_step=3)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     bid = bid.filter(Q(id=search))
                bid = bid.annotate(user_name=Concat('user__first_name', V(', '), 'user__last_name', output_field=CharField())).filter(Q(user_name__icontains=search) | Q(user__user_type__user_type__icontains=search) | Q(user__email__icontains=search) | Q(user__phone_no__icontains=search) | Q(ip_address__icontains=search) | Q(auction__start_price__icontains=search))
            total = bid.count()
            bid = bid.order_by("-id").only("id")[offset: limit]
            if step == "dutch":
                serializer = SuperAdminDutchInsiderBidderSerializer(bid, many=True)
            elif step == "sealed":
                serializer = SuperAdminSealedInsiderBidderSerializer(bid, many=True)
            elif step == "english":
                serializer = SuperAdminEnglishInsiderBidderSerializer(bid, many=True)
            all_data = {
                "property_address": property_address,
                "property_image": property_image,
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SSuperAdminInlineBiddingMonitorView(APIView):
    """
    Super admin inline bidding monitor
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).exclude(user_type=3).first()
                # user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid_registration = BidRegistration.objects.filter(Q(domain=site_id) & Q(user=user_id) & Q(property__sale_by_type=2)).exclude(Q(status__in=[2, 5]) | Q(property__status=5))
            # -------Filter-------
            if "asset_type" in data and data['asset_type'] != "":
                asset_type = int(data['asset_type'])
                bid_registration = bid_registration.filter(property__property_asset=asset_type)

            if "filter_data" in data and data['filter_data'] != "":
                if int(data['filter_data']) == 1:  # ----------For pending------------
                    bid_registration = bid_registration.filter(is_approved=1)
                elif int(data['filter_data']) == 2:  # ----------For approved------------
                    bid_registration = bid_registration.filter(is_approved=2)
                elif int(data['filter_data']) == 3:  # ----------For rejected------------
                    bid_registration = bid_registration.filter(is_approved=3)
                elif int(data['filter_data']) == 4:  # ----------For reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=1)
                elif int(data['filter_data']) == 5:  # ----------For not reviewed------------
                    bid_registration = bid_registration.filter(is_reviewed=0)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    bid_registration = bid_registration.filter(Q(id=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search))
                else:
                    bid_registration = bid_registration.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('view_bid_registration_address_registration__first_name', V(' '), 'view_bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(view_bid_registration_address_registration__first_name__icontains=search) | Q(view_bid_registration_address_registration__last_name__icontains=search) | Q(view_bid_registration_address_registration__phone_no__icontains=search) | Q(view_bid_registration_address_registration__email__icontains=search) | Q(domain__domain_name__icontains=search) | Q(ip_address__icontains=search) | Q(property_name__icontains=search) | Q(view_bid_registration_address_registration__city__icontains=search))
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset:limit]
            serializer = InlineBiddingListingSerializer(bid_registration, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminInlineBiddingMonitorView(APIView):
    """
    Super admin inline bidding monitor
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

            # is_super_admin = None
            # if "is_super_admin" in data and data['is_super_admin'] != "":
            #     is_super_admin = int(data['is_super_admin'])
            #
            # if "domain_id" in data and data['domain_id'] != "":
            #     domain_id = int(data['domain_id'])
            #     network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
            #     if network is None:
            #         return Response(response.parsejson("Site not exist.", "", status=403))
            # else:
            #     if is_super_admin is None:
            #         return Response(response.parsejson("domain_id is required", "", status=403))
            #     else:
            #         domain_id = None

            domain_id = None
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']

            domain_id = None
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            property_data = PropertyListing.objects.filter(sale_by_type=2, is_approved=1)
            if domain_id is not None:
                property_data = property_data.filter(domain=domain_id)

            if "status" in data and data['status'] != "":
                status = int(data['status'])
                # property_data = property_data.filter(Q(status=status))
                if status == 1:
                    property_data = property_data.filter(Q(status=1) & Q(property_auction__start_date__lte=timezone.now()))
                    # property_data = property_data.filter(Q(status=1))
                elif status == 17:
                    property_data = property_data.filter(Q(status=1) & Q(property_auction__start_date__gt=timezone.now()))
                else:
                    property_data = property_data.filter(Q(status=status))

            # -----------------Filter-------------------
            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_data = property_data.filter(Q(agent=agent_id))

            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_data = property_data.filter(Q(sale_by_type=auction_id))

            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                property_data = property_data.filter(Q(property_asset=asset_id))

            if "property_type" in data and data["property_type"] != "":
                property_type = int(data["property_type"])
                property_data = property_data.filter(Q(property_type=property_type))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_data = property_data.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_data = property_data.annotate(
                    property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '),
                                         'postal_code', output_field=CharField())).annotate(
                    full_name=Concat('agent__user_business_profile__first_name', V(' '),
                                     'agent__user_business_profile__last_name')).filter(
                    Q(property_asset__name__icontains=search) | Q(sale_by_type__auction_type__icontains=search) | Q(
                        agent__user_business_profile__company_name__icontains=search) | Q(
                        full_name__icontains=search) | Q(city__icontains=search) | Q(
                        address_one__icontains=search) | Q(state__state_name__icontains=search) | Q(
                        property_type__property_type__icontains=search) | Q(property_name__icontains=search))

            total = property_data.count()
            property_data = property_data.order_by(F("ordering").asc(nulls_last=True)).only("id")[offset:limit]
            serializer = SuperAdminInlineBiddingMonitorSerializer(property_data, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainInlineBiddingMonitorView(APIView):
    """
    Super admin inline bidding monitor
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

            # is_super_admin = None
            # if "is_super_admin" in data and data['is_super_admin'] != "":
            #     is_super_admin = int(data['is_super_admin'])
            #
            # if "domain_id" in data and data['domain_id'] != "":
            #     domain_id = int(data['domain_id'])
            #     network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
            #     if network is None:
            #         return Response(response.parsejson("Site not exist.", "", status=403))
            # else:
            #     if is_super_admin is None:
            #         return Response(response.parsejson("domain_id is required", "", status=403))
            #     else:
            #         domain_id = None

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']
            else:
                return Response(response.parsejson("domain_id is required.", "", status=403))

            # if "agent_id" in data and data['agent_id'] != "":
            #     agent_id = data['agent_id']
            # else:
            #     return Response(response.parsejson("agent_id is required.", "", status=403))

            agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            property_data = PropertyListing.objects.filter(domain=domain_id, sale_by_type=2, is_approved=1)
            if agent is not None:
                property_data = property_data.filter(agent=user_id)

            if "status" in data and data['status'] != "":
                status = int(data['status'])
                property_data = property_data.filter(Q(status=status))

            # -----------------Filter-------------------
            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_data = property_data.filter(Q(agent=agent_id))

            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_data = property_data.filter(Q(sale_by_type=auction_id))

            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                property_data = property_data.filter(Q(property_asset=asset_id))

            if "property_type" in data and data["property_type"] != "":
                property_type = int(data["property_type"])
                property_data = property_data.filter(Q(property_type=property_type))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_data = property_data.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_data = property_data.annotate(
                    property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '),
                                         'postal_code', output_field=CharField())).annotate(
                    full_name=Concat('agent__user_business_profile__first_name', V(' '),
                                     'agent__user_business_profile__last_name')).filter(
                    Q(property_asset__name__icontains=search) | Q(sale_by_type__auction_type__icontains=search) | Q(
                        agent__user_business_profile__company_name__icontains=search) | Q(
                        full_name__icontains=search) | Q(city__icontains=search) | Q(
                        address_one__icontains=search) | Q(state__state_name__icontains=search) | Q(
                        property_type__property_type__icontains=search) | Q(property_name__icontains=search))

            total = property_data.count()
            property_data = property_data.order_by(F("ordering").asc(nulls_last=True)).only("id")[offset:limit]
            serializer = SubdomainInlineBiddingMonitorSerializer(property_data, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NewBidsRegistrationView(APIView):
    """
    New Bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            all_property = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                data['property'] = int(data['property_id'])
                property_portfolio = PropertyPortfolio.objects.filter(property=property_id, portfolio__status=1).first()
                if property_portfolio is not None:
                    property_portfolio = PropertyPortfolio.objects.filter(portfolio=property_portfolio.portfolio_id, property__status=1, property__is_approved=1)
                    all_property = [i.property_id for i in property_portfolio]
                else:
                    all_property = [property_id]
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            if len(all_property) == 1:
                for p_id in all_property:
                    property_data = PropertyListing.objects.filter(id=p_id, domain=domain).first()
                    if property_data is None:
                        return Response(response.parsejson("Listing not available.", "", status=403))
                    if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 6 or property_data.sale_by_type_id == 7:
                        return Response(response.parsejson("This property not for auction", "", status=403))
                    # if property_data.agent_id == user_id:
                    #     return Response(response.parsejson("You are owner of property.", "", status=403))
                    if property_data.status_id != 1:
                        return Response(response.parsejson("Listing not active.", "", status=403))
                    if not property_data.is_approved:
                        return Response(response.parsejson("Listing not approved.", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if user_type == 2:  # -----------Buyer-------------
                if "working_with_agent" in data and data['working_with_agent'] != "":
                    working_with_agent = int(data['working_with_agent'])
                    if working_with_agent == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                else:
                    return Response(response.parsejson("working_with_agent is required", "", status=403))
            elif user_type == 4:  # -----------Agent-------------
                if "property_yourself" in data and data['property_yourself'] != "":
                    property_yourself = int(data['property_yourself'])
                    if property_yourself == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(
                                data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_seller_address" in data and type(data['buyer_seller_address']) == dict and len(data['buyer_seller_address']) > 0:
                            buyer_seller_address = data['buyer_seller_address']
                            if "first_name" in buyer_seller_address and buyer_seller_address['first_name'] != "":
                                buyer_seller_address_first_name = buyer_seller_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->first_name is required", "", status=403))

                            if "last_name" in buyer_seller_address and buyer_seller_address['last_name'] != "":
                                buyer_seller_address_last_name = buyer_seller_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->last_name is required", "", status=403))

                            if "email" in buyer_seller_address and buyer_seller_address['email'] != "":
                                buyer_seller_address_email = buyer_seller_address['email']
                            else:
                                return Response(response.parsejson("buyer_seller_address->email is required", "", status=403))

                            if "phone_no" in buyer_seller_address and buyer_seller_address['phone_no'] != "":
                                buyer_seller_address_phone_no = buyer_seller_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_seller_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_seller_address and buyer_seller_address['address_first'] != "":
                                buyer_seller_address_first = buyer_seller_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in buyer_seller_address and buyer_seller_address['city'] != "":
                                buyer_seller_address_city = buyer_seller_address['city']
                            else:
                                return Response(response.parsejson("buyer_seller_address->city is required", "", status=403))

                            if "state" in buyer_seller_address and buyer_seller_address['state'] != "":
                                buyer_seller_address_state = int(buyer_seller_address['state'])
                            else:
                                return Response(response.parsejson("buyer_seller_address->state is required", "", status=403))

                            if "postal_code" in buyer_seller_address and buyer_seller_address['postal_code'] != "":
                                buyer_seller_address_postal_code = buyer_seller_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_seller_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_seller_address is required", "", status=403))
                else:
                    return Response(response.parsejson("property_yourself is required", "", status=403))

            if "term_accepted" in data and data['term_accepted'] != "":
                if int(data['term_accepted']) == 1:
                    data['term_accepted'] = int(data['term_accepted'])
                else:
                    return Response(response.parsejson("term not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("term_accepted is required", "", status=403))

            if "age_accepted" in data and data['age_accepted'] != "":
                if int(data['age_accepted']) == 1:
                    data['age_accepted'] = int(data['age_accepted'])
                else:
                    return Response(response.parsejson("age not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("age_accepted is required", "", status=403))

            # if "correct_info" in data and data['correct_info'] != "":
            #     if int(data['correct_info']) == 1:
            #         data['correct_info'] = int(data['correct_info'])
            #     else:
            #         return Response(response.parsejson("User has not correct info.", "", status=403))
            # else:
            #     return Response(response.parsejson("correct_info is required", "", status=403))

            if "upload_pof" in data and data['upload_pof'] != "":
                upload_pof = int(data['upload_pof'])
            else:
                return Response(response.parsejson("upload_pof is required", "", status=403))

            uploads = None
            if upload_pof == 1:
                data['reason_for_not_upload'] = None
                if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
                    uploads = data['uploads']
                else:
                    return Response(response.parsejson("uploads is required", "", status=403))
            else:
                if "reason_for_not_upload" in data and data['reason_for_not_upload'] != "":
                    reason_for_not_upload = data['reason_for_not_upload']
                else:
                    return Response(response.parsejson("reason_for_not_upload is required", "", status=403))

            if "ip_address" in data and data['ip_address'] != "":
                ip_address = data['ip_address']
            else:
                return Response(response.parsejson("ip_address is required", "", status=403))

            data['status'] = 1
            registration_data = None
            with transaction.atomic():
                for p_id in all_property:

                    property_data = PropertyListing.objects.filter(id=p_id, domain=domain).first()
                    if property_data is None:
                        # return Response(response.parsejson("Listing not available.", "", status=403))
                        continue
                    if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 6 or property_data.sale_by_type_id == 7:
                        # return Response(response.parsejson("This property not for auction", "", status=403))
                        continue
                    # if property_data.agent_id == user_id:
                    #     return Response(response.parsejson("You are owner of property.", "", status=403))
                    if property_data.status_id != 1:
                        # return Response(response.parsejson("Listing not active.", "", status=403))
                        continue
                    if not property_data.is_approved:
                        # return Response(response.parsejson("Listing not approved.", "", status=403))
                        continue

                    bid_registration = BidRegistration.objects.filter(domain=domain, user=user_id, property=p_id, status=1).first()
                    if bid_registration is not None:
                        # return Response(response.parsejson("Already requested to registration.", "", status=403))
                        continue

                    # -----------------------Check auto approve--------------
                    property_settings = PropertySettings.objects.filter(domain=domain, property=p_id, is_broker=0, is_agent=0, status=1).first()
                    auto_approve = None
                    approval_limit = None
                    if property_settings is not None:
                        if property_settings.auto_approval == 1:
                            auto_approve = True
                            approval_limit = property_settings.bid_limit
                            data['is_reviewed'] = 1
                            data['is_approved'] = 2
                            data['seller_comment'] = "Auto approve"
                    else:
                        property_settings = PropertySettings.objects.filter(domain=domain, is_agent=1, is_broker=0, status=1).first()
                        if property_settings is not None:
                            if property_settings.auto_approval == 1:
                                auto_approve = True
                                approval_limit = property_settings.bid_limit
                                data['is_reviewed'] = 1
                                data['is_approved'] = 2
                                data['seller_comment'] = "Auto approve"
                        else:
                            property_settings = PropertySettings.objects.filter(domain=domain, is_broker=1, is_agent=0, status=1).first()
                            if property_settings is not None and property_settings.auto_approval == 1:
                                auto_approve = True
                                approval_limit = property_settings.bid_limit
                                data['is_reviewed'] = 1
                                data['is_approved'] = 2
                                data['seller_comment'] = "Auto approve"

                    registration_id = unique_registration_id()  # Get unique registration id
                    if registration_id:
                        data['registration_id'] = registration_id
                    else:
                        return Response(response.parsejson("Registration id not generated.", "", status=403))
                    # with transaction.atomic():
                    data['property'] = p_id
                    serializer = BidRegistrationSerializer(data=data)
                    if serializer.is_valid():
                        registration_id = serializer.save()
                        registration_id = registration_id.id
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
                    if auto_approve is not None:
                        try:
                            bid_limit = BidLimit()
                            bid_limit.registration_id = registration_id
                            bid_limit.status_id = 1
                            bid_limit.approval_limit = approval_limit
                            bid_limit.is_approved = 2
                            bid_limit.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))
                    try:
                        if uploads is not None and len(uploads) > 0:
                            for upload in uploads:
                                proof_funds = ProofFunds()
                                proof_funds.registration_id = registration_id
                                proof_funds.upload_id = upload
                                proof_funds.status_id = 1
                                proof_funds.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))
                    registration_data = {}
                    if user_type == 2:
                        registration_data['first_name'] = buyer_address['first_name']
                        registration_data['last_name'] = buyer_address['last_name']
                        registration_data['email'] = buyer_address['email']
                        registration_data['phone_no'] = buyer_address['phone_no']

                        if working_with_agent == 1:
                            agent_address['address_type'] = 1
                            agent_address['registration'] = registration_id
                            agent_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=agent_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                    elif user_type == 4:
                        if property_yourself == 1:
                            registration_data['first_name'] = buyer_address['first_name']
                            registration_data['last_name'] = buyer_address['last_name']
                            registration_data['email'] = buyer_address['email']
                            registration_data['phone_no'] = buyer_address['phone_no']

                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                            agent_address['address_type'] = 1
                            agent_address['registration'] = registration_id
                            agent_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=agent_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            registration_data['first_name'] = buyer_seller_address['first_name']
                            registration_data['last_name'] = buyer_seller_address['last_name']
                            registration_data['email'] = buyer_seller_address['email']
                            registration_data['phone_no'] = buyer_seller_address['phone_no']

                            buyer_seller_address['address_type'] = 3
                            buyer_seller_address['registration'] = registration_id
                            buyer_seller_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_seller_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                    try:
                        bid_registration_data = BidRegistration.objects.get(id=registration_id)
                        serializer = BidRegistrationSerializer(bid_registration_data, data=registration_data)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), "", status=403))

                    try:
                        property_detail = PropertyListing.objects.get(id=p_id)
                        agent_detail = property_detail.agent
                        agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                        agent_email = agent_detail.email if agent_detail.email is not None else ""
                        agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                        buyer_detail = Users.objects.get(id=user_id)
                        buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                        buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                        buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                        broker_detail = Users.objects.get(site_id=domain)
                        broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                        broker_email = broker_detail.email if broker_detail.email is not None else ""
                        broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                        property_address = property_detail.address_one if property_detail.address_one is not None else ""
                        property_city = property_detail.city if property_detail.city is not None else ""
                        property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                        upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                        web_url = settings.FRONT_BASE_URL
                        image_url = web_url+'/static/admin/images/property-default-img.png'
                        image = ''
                        bucket_name = ''
                        if upload is not None:
                            image = upload.upload.doc_file_name if upload.upload.doc_file_name is not None else ""
                            bucket_name = upload.upload.bucket_name if upload.upload.bucket_name is not None else ""
                            image_url = settings.AWS_URL+bucket_name+'/'+image
                        subdomain_url = settings.SUBDOMAIN_URL
                        domain_name = network.domain_name

                        #=========================Send email to buyer====================
                        domain_detail = NetworkDomain.objects.filter(id=domain).first()
                        template_data = {"domain_id": domain, "slug": "bid_registration"}
                        if domain_detail.domain_type == 1:
                            domain_url = domain_detail.domain_url+"asset-details/?property_id="+str(p_id)
                        else:
                            domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(p_id)
                        extra_data = {'user_name': buyer_name,
                                    'web_url': web_url,
                                    'property_image': image_url,
                                    'property_address': property_address,
                                    'property_city': property_city,
                                    'property_state': property_state,
                                    'prop_link': domain_url,
                                    "domain_id": domain,
                                    'agent_name': agent_name,
                                    'agent_email': agent_email,
                                    'agent_phone': phone_format(agent_phone)
                                }
                        compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                        #========================Send email to agent=========================
                        if agent_email.lower() != buyer_email.lower():
                            template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                            if domain_detail.domain_type == 1:
                                domain_url = domain_detail.domain_url+"admin/bidder-registration/"
                            else:
                                domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                            extra_data = {'user_name': agent_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                            compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                        #========================Send email to broker========================
                        if broker_email.lower() != agent_email.lower():
                            if domain_detail.domain_type == 1:
                                domain_url = domain_detail.domain_url+"admin/bidder-registration/"
                            else:
                                domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                            template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                            extra_data = {'user_name': broker_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                            compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                        if auto_approve:
                            template_data = {"domain_id": domain, "slug": "bid_registration_approval"}
                            domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(p_id)
                            extra_data = {'user_name': buyer_name, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, 'domain_id': domain, 'status': 'approved'}
                            compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
                    except Exception as e:
                        pass

                    try:
                        prop_name = property_data.address_one if property_data.address_one else property_data.id
                        #  add notfification to buyer
                        content = "Your registration has been sent!! <span>[" + prop_name + "]</span>"
                        add_notification(
                            domain,
                            "Bid Registration",
                            content,
                            user_id=user_id,
                            added_by=user_id,
                            notification_for=1,
                            property_id=p_id
                        )
                        if user_id != property_data.agent_id:
                            #  add notfification to seller/agent
                            content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                            add_notification(
                                domain,
                                "Bid Registration",
                                content,
                                user_id=property_data.agent_id,
                                added_by=property_data.agent_id,
                                notification_for=2,
                                property_id=p_id
                            )
                        # if user_id != property_data.agent_id and user_id != broker_detail.id:
                        if property_data.agent_id != broker_detail.id:
                            content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                            add_notification(
                                domain,
                                "Bid Registration",
                                content,
                                user_id=broker_detail.id,
                                added_by=broker_detail.id,
                                notification_for=2,
                                property_id=p_id
                            )
                        # send approval notif if auto approval on
                        if auto_approve:
                            content = "Your registration has been approved! <span>[" + prop_name + "]</span>"
                            add_notification(
                                domain,
                                "Bid Registration",
                                content,
                                user_id=user_id,
                                added_by=user_id,
                                notification_for=1,
                                property_id=p_id
                            )

                    except Exception as e:
                        pass
                    registration_data = {"registration_id": registration_id}
            if registration_data is None:
                return Response(response.parsejson("Already requested to registration.", "", status=403))
            else:
                return Response(response.parsejson("Registration successfully.", registration_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DepositBidsRegistrationView(APIView):
    """
    Deposit Bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            all_property = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                all_property = [property_id]
                # data['property'] = int(data['property_id'])
                # property_portfolio = PropertyPortfolio.objects.filter(property=property_id, portfolio__status=1).first()
                # if property_portfolio is not None:
                #     property_portfolio = PropertyPortfolio.objects.filter(portfolio=property_portfolio.portfolio_id, property__status=1, property__is_approved=1)
                #     all_property = [i.property_id for i in property_portfolio]
                # else:
                #     all_property = [property_id]
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "term_accepted" in data and data['term_accepted'] != "":
                if int(data['term_accepted']) == 1:
                    data['term_accepted'] = int(data['term_accepted'])
                else:
                    return Response(response.parsejson("term not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("term_accepted is required", "", status=403))

            if "age_accepted" in data and data['age_accepted'] != "":
                if int(data['age_accepted']) == 1:
                    data['age_accepted'] = int(data['age_accepted'])
                else:
                    return Response(response.parsejson("age not accepted by user.", "", status=403))
            else:
                return Response(response.parsejson("age_accepted is required", "", status=403))  

            if "ip_address" in data and data['ip_address'] != "":
                ip_address = data['ip_address']
            else:
                return Response(response.parsejson("ip_address is required", "", status=403))  

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if "session_id" in data and data['session_id'] != "":
                session_id = data['session_id']
            else:
                return Response(response.parsejson("session_id is required", "", status=403))

            if "deposit_amount" in data and data['deposit_amount'] != "":
                deposit_amount = int(float(data['deposit_amount']))
            else:
                return Response(response.parsejson("deposit_amount is required", "", status=403))   


            property_data = PropertyListing.objects.filter(id=property_id, domain=domain).first()
            if property_data is None:
                return Response(response.parsejson("Listing not available.", "", status=403))
            if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 6 or property_data.sale_by_type_id == 7:
                return Response(response.parsejson("This property not for auction", "", status=403))
            if property_data.status_id != 1:
                return Response(response.parsejson("Listing not active.", "", status=403))
            if not property_data.is_approved:
                return Response(response.parsejson("Listing not approved.", "", status=403))           
            
            # if len(all_property) == 1:
            #     for p_id in all_property:
            #         property_data = PropertyListing.objects.filter(id=p_id, domain=domain).first()
            #         if property_data is None:
            #             return Response(response.parsejson("Listing not available.", "", status=403))
            #         if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 6 or property_data.sale_by_type_id == 7:
            #             return Response(response.parsejson("This property not for auction", "", status=403))
            #         # if property_data.agent_id == user_id:
            #         #     return Response(response.parsejson("You are owner of property.", "", status=403))
            #         if property_data.status_id != 1:
            #             return Response(response.parsejson("Listing not active.", "", status=403))
            #         if not property_data.is_approved:
            #             return Response(response.parsejson("Listing not approved.", "", status=403))
            
            if user_type == 2:  # -----------Buyer-------------
                if "working_with_agent" in data and data['working_with_agent'] != "":
                    working_with_agent = int(data['working_with_agent'])
                    if working_with_agent == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(
                                    response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))  
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                else:
                    return Response(response.parsejson("working_with_agent is required", "", status=403))
            elif user_type == 4:  # -----------Agent-------------
                if "property_yourself" in data and data['property_yourself'] != "":
                    property_yourself = int(data['property_yourself'])
                    if property_yourself == 1:
                        if "agent_address" in data and type(data['agent_address']) == dict and len(
                                data['agent_address']) > 0:
                            agent_address = data['agent_address']
                            if "first_name" in agent_address and agent_address['first_name'] != "":
                                agent_first_name = agent_address['first_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->first_name is required", "", status=403))

                            if "last_name" in agent_address and agent_address['last_name'] != "":
                                agent_last_name = agent_address['last_name']
                            else:
                                return Response(
                                    response.parsejson("agent_address->last_name is required", "", status=403))

                            if "email" in agent_address and agent_address['email'] != "":
                                agent_email = agent_address['email']
                            else:
                                return Response(response.parsejson("agent_address->email is required", "", status=403))

                            if "phone_no" in agent_address and agent_address['phone_no'] != "":
                                agent_phone_no = agent_address['phone_no']
                            else:
                                return Response(response.parsejson("agent_address->phone_no is required", "", status=403))

                            if "address_first" in agent_address and agent_address['address_first'] != "":
                                agent_address_first = agent_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in agent_address and agent_address['city'] != "":
                                agent_city = agent_address['city']
                            else:
                                return Response(response.parsejson("agent_address->city is required", "", status=403))

                            if "state" in agent_address and agent_address['state'] != "":
                                agent_state = int(agent_address['state'])
                            else:
                                return Response(response.parsejson("agent_address->state is required", "", status=403))

                            if "postal_code" in agent_address and agent_address['postal_code'] != "":
                                agent_postal_code = agent_address['postal_code']
                            else:
                                return Response(response.parsejson("agent_address->postal_code is required", "", status=403))

                            if "company_name" in agent_address and agent_address['company_name'] != "":
                                agent_company_name = agent_address['company_name']
                            else:
                                return Response(response.parsejson("agent_address->company_name is required", "", status=403))
                        else:
                            return Response(response.parsejson("agent_address is required", "", status=403))

                        if "buyer_address" in data and type(data['buyer_address']) == dict and len(data['buyer_address']) > 0:
                            buyer_address = data['buyer_address']
                            if "first_name" in buyer_address and buyer_address['first_name'] != "":
                                buyer_first_name = buyer_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "last_name" in buyer_address and buyer_address['last_name'] != "":
                                buyer_last_name = buyer_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_address->last_name is required", "", status=403))

                            if "email" in buyer_address and buyer_address['email'] != "":
                                buyer_email = buyer_address['email']
                            else:
                                return Response(response.parsejson("buyer_address->email is required", "", status=403))

                            if "phone_no" in buyer_address and buyer_address['phone_no'] != "":
                                buyer_phone_no = buyer_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_address and buyer_address['address_first'] != "":
                                buyer_address_first = buyer_address['address_first']
                            else:
                                return Response(response.parsejson("buyer_address->address_first is required", "", status=403))

                            if "city" in buyer_address and buyer_address['city'] != "":
                                buyer_city = buyer_address['city']
                            else:
                                return Response(response.parsejson("buyer_address->city is required", "", status=403))

                            if "state" in buyer_address and buyer_address['state'] != "":
                                buyer_state = int(buyer_address['state'])
                            else:
                                return Response(response.parsejson("buyer_address->state is required", "", status=403))

                            if "postal_code" in buyer_address and buyer_address['postal_code'] != "":
                                buyer_postal_code = buyer_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_address is required", "", status=403))
                    else:
                        if "buyer_seller_address" in data and type(data['buyer_seller_address']) == dict and len(data['buyer_seller_address']) > 0:
                            buyer_seller_address = data['buyer_seller_address']
                            if "first_name" in buyer_seller_address and buyer_seller_address['first_name'] != "":
                                buyer_seller_address_first_name = buyer_seller_address['first_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->first_name is required", "", status=403))

                            if "last_name" in buyer_seller_address and buyer_seller_address['last_name'] != "":
                                buyer_seller_address_last_name = buyer_seller_address['last_name']
                            else:
                                return Response(response.parsejson("buyer_seller_address->last_name is required", "", status=403))

                            if "email" in buyer_seller_address and buyer_seller_address['email'] != "":
                                buyer_seller_address_email = buyer_seller_address['email']
                            else:
                                return Response(response.parsejson("buyer_seller_address->email is required", "", status=403))

                            if "phone_no" in buyer_seller_address and buyer_seller_address['phone_no'] != "":
                                buyer_seller_address_phone_no = buyer_seller_address['phone_no']
                            else:
                                return Response(response.parsejson("buyer_seller_address->phone_no is required", "", status=403))

                            if "address_first" in buyer_seller_address and buyer_seller_address['address_first'] != "":
                                buyer_seller_address_first = buyer_seller_address['address_first']
                            else:
                                return Response(response.parsejson("agent_address->address_first is required", "", status=403))

                            if "city" in buyer_seller_address and buyer_seller_address['city'] != "":
                                buyer_seller_address_city = buyer_seller_address['city']
                            else:
                                return Response(response.parsejson("buyer_seller_address->city is required", "", status=403))

                            if "state" in buyer_seller_address and buyer_seller_address['state'] != "":
                                buyer_seller_address_state = int(buyer_seller_address['state'])
                            else:
                                return Response(response.parsejson("buyer_seller_address->state is required", "", status=403))

                            if "postal_code" in buyer_seller_address and buyer_seller_address['postal_code'] != "":
                                buyer_seller_address_postal_code = buyer_seller_address['postal_code']
                            else:
                                return Response(response.parsejson("buyer_seller_address->postal_code is required", "", status=403))
                        else:
                            return Response(response.parsejson("buyer_seller_address is required", "", status=403))
                else:
                    return Response(response.parsejson("property_yourself is required", "", status=403))

            # if "upload_pof" in data and data['upload_pof'] != "":
            #     upload_pof = int(data['upload_pof'])
            # else:
            #     return Response(response.parsejson("upload_pof is required", "", status=403))

            # uploads = None
            # if upload_pof == 1:
            #     data['reason_for_not_upload'] = None
            #     if "uploads" in data and type(data['uploads']) == list and len(data['uploads']) > 0:
            #         uploads = data['uploads']
            #     else:
            #         return Response(response.parsejson("uploads is required", "", status=403))
            # else:
            #     if "reason_for_not_upload" in data and data['reason_for_not_upload'] != "":
            #         reason_for_not_upload = data['reason_for_not_upload']
            #     else:
            #         return Response(response.parsejson("reason_for_not_upload is required", "", status=403))

            data['status'] = 2
            registration_data = None
            with transaction.atomic():
                for p_id in all_property:

                    property_data = PropertyListing.objects.filter(id=p_id, domain=domain).first()
                    if property_data is None:
                        return Response(response.parsejson("Listing not available.", "", status=403))
                        # continue
                    if property_data.sale_by_type_id == 4 or property_data.sale_by_type_id == 6 or property_data.sale_by_type_id == 7:
                        return Response(response.parsejson("This property not for auction", "", status=403))
                        # continue
                    # if property_data.agent_id == user_id:
                    #     return Response(response.parsejson("You are owner of property.", "", status=403))
                    if property_data.status_id != 1:
                        return Response(response.parsejson("Listing not active.", "", status=403))
                        # continue
                    if not property_data.is_approved:
                        return Response(response.parsejson("Listing not approved.", "", status=403))
                        # continue

                    bid_registration = BidRegistration.objects.filter(domain=domain, user=user_id, property=p_id, status=1).first()
                    if bid_registration is not None:
                        return Response(response.parsejson("Already requested to registration.", "", status=403))
                        # continue

                    auto_approve = True
                    approval_limit = 1000000
                    data['is_reviewed'] = 0
                    data['is_approved'] = 1
                    data['seller_comment'] = "Approval Pending"

                    registration_id = unique_registration_id()  # Get unique registration id
                    if registration_id:
                        data['registration_id'] = registration_id
                    else:
                        return Response(response.parsejson("Registration id not generated.", "", status=403))
                    # with transaction.atomic():
                    data['property'] = p_id
                    
                    serializer = BidRegistrationSerializer(data=data)
                    if serializer.is_valid():
                        registration_id = serializer.save()
                        registration_id = registration_id.id
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
                    if auto_approve is not None:
                        try:
                            bid_limit = BidLimit()
                            bid_limit.registration_id = registration_id
                            bid_limit.status_id = 1
                            bid_limit.approval_limit = approval_limit
                            bid_limit.is_approved = 2
                            bid_limit.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))
                    
                    registration_data = {}
                    if user_type == 2:
                        registration_data['first_name'] = buyer_address['first_name']
                        registration_data['last_name'] = buyer_address['last_name']
                        registration_data['email'] = buyer_address['email']
                        registration_data['phone_no'] = buyer_address['phone_no']

                        if working_with_agent == 1:
                            agent_address['address_type'] = 1
                            agent_address['registration'] = registration_id
                            agent_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=agent_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                    elif user_type == 4:
                        if property_yourself == 1:
                            registration_data['first_name'] = buyer_address['first_name']
                            registration_data['last_name'] = buyer_address['last_name']
                            registration_data['email'] = buyer_address['email']
                            registration_data['phone_no'] = buyer_address['phone_no']

                            buyer_address['address_type'] = 2
                            buyer_address['registration'] = registration_id
                            buyer_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                            agent_address['address_type'] = 1
                            agent_address['registration'] = registration_id
                            agent_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=agent_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            registration_data['first_name'] = buyer_seller_address['first_name']
                            registration_data['last_name'] = buyer_seller_address['last_name']
                            registration_data['email'] = buyer_seller_address['email']
                            registration_data['phone_no'] = buyer_seller_address['phone_no']

                            buyer_seller_address['address_type'] = 3
                            buyer_seller_address['registration'] = registration_id
                            buyer_seller_address['status'] = 1
                            serializer = BidRegistrationAddressSerializer(data=buyer_seller_address)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                    try:
                        bid_registration_data = BidRegistration.objects.get(id=registration_id)
                        serializer = BidRegistrationSerializer(bid_registration_data, data=registration_data)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), "", status=403))

                    registration_data = {"registration_id": registration_id}
            if registration_data is None:
                return Response(response.parsejson("Already requested to registration.", "", status=403))
            else:
                return Response(response.parsejson("Registration successfully.", registration_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendEnglishAuctionEmailView(APIView):
    """
    Send english auction email
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "bid_amount" in data and data['bid_amount'] != "":
                bid_amount = int(data['bid_amount'])
            else:
                return Response(response.parsejson("bid_amount is required", "", status=403))

            user = Users.objects.get(id=user_id)
            auction_data = PropertyAuction.objects.get(property=property_id)
            upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
            broker_detail = Users.objects.get(site_id=domain_id)
            if upload is not None:
                image_url = settings.AWS_URL + upload.upload.bucket_name + '/' + upload.upload.doc_file_name
            else:
                image_url = settings.FRONT_BASE_URL + '/static/admin/images/property-default-img.png'
            domain_url = settings.SUBDOMAIN_URL.replace("###", auction_data.domain.domain_name) + "asset-details/?property_id=" + str(property_id)

            # send email to buyer
            extra_data = {
                "user_name": user.first_name + ' ' + user.last_name,
                'property_address': auction_data.property.address_one,
                'property_city': auction_data.property.city,
                'property_state': auction_data.property.state.state_name,
                'property_zipcode': auction_data.property.postal_code,
                'auction_type': auction_data.property.sale_by_type.auction_type,
                'asset_type': auction_data.property.property_asset.name,
                'starting_price': number_format(auction_data.start_price),
                'property_image': image_url,
                'dashboard_link': domain_url,
                "domain_id": domain_id,
                "bid_amount": number_format(bid_amount)
            }
            # ------English Winner User Email------
            template_data = {"domain_id": domain_id, "slug": "english_auction_winner"}
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)

            # ------English Lost User Email------
            registration = BidRegistration.objects.filter(domain=domain_id, property=property_id, is_reviewed=1, is_approved=2).exclude(user=user_id)
            if registration is not None:
                for reg in registration:
                    # user = Users.objects.get(id=lost_user_id)
                    extra_data["user_name"] = reg.user.first_name + ' ' + reg.user.last_name
                    template_data = {"domain_id": domain_id, "slug": "english_auction_lost"}
                    compose_email(to_email=[reg.user.email], template_data=template_data, extra_data=extra_data)

            return Response(response.parsejson("Mail sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserBidHistoryView(APIView):
    """
    User bid history
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            register_user = None
            if "register_user" in data and data['register_user'] != "":
                register_user = int(data['register_user'])

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(Q(id=user_id) & Q(status=1) & (Q(site=site_id) | (Q(network_user__domain=site_id) & Q(network_user__status=1)))).exclude(user_type=3).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            bid = Bid.objects.filter(Q(domain=site_id) & Q(property=property_id) & Q(is_canceled=0) & Q(bid_type__in=[2, 3]))
            if register_user is not None:
                bid = bid.filter(user=register_user)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    # bid = bid.filter(Q(id=search) | Q(user__phone_no__icontains=search) | Q(bid_amount__icontains=search))
                    bid = bid.filter(Q(id=search) | Q(registration__bid_registration_address_registration__phone_no__icontains=search) | Q(bid_amount__icontains=search))
                else:
                    # bid = bid.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(user__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
                    bid = bid.annotate(full_name=Concat('registration__bid_registration_address_registration__first_name', V(' '), 'registration__bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(registration__bid_registration_address_registration__first_name__icontains=search) | Q(registration__bid_registration_address_registration__last_name__icontains=search) | Q(registration__bid_registration_address_registration__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
            bid = bid.distinct("id")
            total = bid.count()
            bid = bid.order_by("-id").only("id")[offset:limit]
            serializer = SubdomainBidHistorySerializer(bid, many=True)

            property_listing = PropertyListing.objects.get(Q(id=property_id) & Q(domain=site_id))
            property_detail = BidPropertyDetailSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TotalBidHistoryView(APIView):
    """
    Total bid history
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
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "bid_id" in data and data['bid_id'] != "":
                bid_id = int(data['bid_id'])
            else:
                return Response(response.parsejson("bid_id is required", "", status=403))


            register_user = None
            if "register_user" in data and data['register_user'] != "":
                register_user = int(data['register_user'])

            bid_data = Bid.objects.filter(id=bid_id).last()

            bid = Bid.objects.filter(Q(domain=site_id) & Q(user=bid_data.user_id) & Q(property=bid_data.property_id) & Q(is_canceled=0) & Q(bid_type__in=[2, 3]))
            if register_user is not None:
                bid = bid.filter(user=register_user)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    # bid = bid.filter(Q(id=search) | Q(user__phone_no__icontains=search) | Q(bid_amount__icontains=search))
                    bid = bid.filter(Q(id=search) | Q(registration__bid_registration_address_registration__phone_no__icontains=search) | Q(bid_amount__icontains=search))
                else:
                    # bid = bid.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(user__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
                    bid = bid.annotate(full_name=Concat('registration__bid_registration_address_registration__first_name', V(' '), 'registration__bid_registration_address_registration__last_name')).filter(Q(full_name__icontains=search) | Q(registration__bid_registration_address_registration__first_name__icontains=search) | Q(registration__bid_registration_address_registration__last_name__icontains=search) | Q(registration__bid_registration_address_registration__email__icontains=search) | Q(bid_amount__icontains=search) | Q(ip_address__icontains=search))
            # bid = bid.distinct("id")
            total = bid.count()
            bid = bid.order_by("-id").only("id")[offset:limit]
            serializer = TotalBidHistorySerializer(bid, many=True, context=bid_data.property_id)

            property_listing = PropertyListing.objects.get(Q(id=bid_data.property_id) & Q(domain=site_id))
            property_detail = BidPropertyDetailSerializer(property_listing)
            all_data = {
                'property_detail': property_detail.data,
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminDeleteBidRegistrationView(APIView):
    """
    Super admin delete bid registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "registration_id" in data and data['registration_id'] != "":
                registration_id = int(data['registration_id'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = Users.objects.filter(Q(id=data['user']) & Q(user_type=3) & Q(status=1)).first()
                if user is None:
                    return Response(response.parsejson("You are not active user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            bid_registration = BidRegistration.objects.filter(Q(id=registration_id) & Q(status=1)).first()
            if bid_registration is None:
                return Response(response.parsejson("Registration not exist.", "", status=403))
            property_id = bid_registration.property_id
            auction_type = bid_registration.property.sale_by_type_id
            bid_count = Bid.objects.filter(registration=bid_registration.id).count()
            if bid_count > 0:
                return Response(response.parsejson("Can't inactive because buyer placed a bid.", "", status=403))
            with transaction.atomic():
                try:
                    bid_registration = BidRegistration.objects.filter(Q(id=registration_id)).update(status_id=2)
                    # if bid_registration is None:
                    #     return Response(response.parsejson("You have not permission to delete.", "", status=403))
                    # bid_registration.status_id = 5
                    # bid_registration.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            property_auction = PropertyAuction.objects.filter(property=property_id).last()
            all_data = {"property_id": property_id, "auction_type": auction_type, "auction_id": property_auction.id}
            return Response(response.parsejson("Deleted successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BidDepositSuccessView(APIView):
    """
    Bid Deposit Success
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "session_id" in data and data['session_id'] != "":
                session_id = data['session_id']
            else:
                return Response(response.parsejson("session_id is required", "", status=403))
            
            bid_registration = BidRegistration.objects.filter(session_id=session_id, status=2).last()
            if bid_registration is None:
                return Response(response.parsejson("Registration not exist.", "", status=403))
            
            bid_registration.status_id = 1
            bid_registration.is_reviewed = 1
            bid_registration.is_approved = 2
            bid_registration.seller_comment = "Auto approved"
            bid_registration.deposit_payment_success = 1
            bid_registration.save()
            all_data = {"property_id": bid_registration.property_id}
            
            # -----------------Email----------------
            try:
                p_id = bid_registration.property_id
                user_id = bid_registration.user_id
                domain = bid_registration.domain_id
                property_id = bid_registration.property_id
                property_detail = PropertyListing.objects.get(id=p_id)
                property_data = PropertyListing.objects.get(id=p_id)
                agent_detail = property_detail.agent
                agent_name = agent_detail.first_name if agent_detail.first_name is not None else ""
                agent_email = agent_detail.email if agent_detail.email is not None else ""
                agent_phone = agent_detail.phone_no if agent_detail.phone_no is not None else ""
                buyer_detail = Users.objects.get(id=user_id)
                buyer_name = buyer_detail.first_name if buyer_detail.first_name is not None else ""
                buyer_email = buyer_detail.email if buyer_detail.email is not None else ""
                buyer_phone = buyer_detail.phone_no if buyer_detail.phone_no is not None else ""
                broker_detail = Users.objects.get(site_id=domain)
                broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                broker_email = broker_detail.email if broker_detail.email is not None else ""
                broker_phone = broker_detail.phone_no if broker_detail.phone_no is not None else ""
                property_address = property_detail.address_one if property_detail.address_one is not None else ""
                property_city = property_detail.city if property_detail.city is not None else ""
                property_state = property_detail.state.state_name if property_detail.state.state_name is not None else ""
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                image = ''
                bucket_name = ''
                if upload is not None:
                    image = upload.upload.doc_file_name if upload.upload.doc_file_name is not None else ""
                    bucket_name = upload.upload.bucket_name if upload.upload.bucket_name is not None else ""
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                subdomain_url = settings.SUBDOMAIN_URL
                # domain_name = network.domain_name

                #=========================Send email to buyer====================
                domain_detail = NetworkDomain.objects.filter(id=domain).first()
                domain_name = domain_detail.domain_name
                template_data = {"domain_id": domain, "slug": "bid_registration"}
                if domain_detail.domain_type == 1:
                    domain_url = domain_detail.domain_url+"asset-details/?property_id="+str(p_id)
                else:
                    domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(p_id)
                extra_data = {'user_name': buyer_name,
                            'web_url': web_url,
                            'property_image': image_url,
                            'property_address': property_address,
                            'property_city': property_city,
                            'property_state': property_state,
                            'prop_link': domain_url,
                            "domain_id": domain,
                            'agent_name': agent_name,
                            'agent_email': agent_email,
                            'agent_phone': phone_format(agent_phone)
                        }
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)

                #========================Send email to agent=========================
                if agent_email.lower() != buyer_email.lower():
                    template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                    if domain_detail.domain_type == 1:
                        domain_url = domain_detail.domain_url+"admin/bidder-registration/"
                    else:
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                    extra_data = {'user_name': agent_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                #========================Send email to broker========================
                if broker_email.lower() != agent_email.lower():
                    if domain_detail.domain_type == 1:
                        domain_url = domain_detail.domain_url+"admin/bidder-registration/"
                    else:
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/bidder-registration/"
                    template_data = {"domain_id": domain, "slug": "bid_registration_agent_broker"}
                    extra_data = {'user_name': broker_name, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, "domain_id": domain, 'buyer_name': buyer_name, 'buyer_email': buyer_email, 'buyer_phone': phone_format(buyer_phone)}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                
                template_data = {"domain_id": domain, "slug": "bid_registration_approval"}
                domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(p_id)
                extra_data = {'user_name': buyer_name, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'dashboard_link': domain_url, 'domain_id': domain, 'status': 'approved'}
                compose_email(to_email=[buyer_email], template_data=template_data, extra_data=extra_data)
            except Exception as e:
                pass

            try:
                prop_name = property_data.address_one if property_data.address_one else property_data.id
                #  add notfification to buyer
                content = "Your registration has been sent!! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain,
                    "Bid Registration",
                    content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    property_id=p_id
                )
                if user_id != property_data.agent_id:
                    #  add notfification to seller/agent
                    content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration",
                        content,
                        user_id=property_data.agent_id,
                        added_by=property_data.agent_id,
                        notification_for=2,
                        property_id=p_id
                    )
                # if user_id != property_data.agent_id and user_id != broker_detail.id:
                if property_data.agent_id != broker_detail.id:
                    content = "Buyers Are Lining Up! <span>[" + prop_name + "]</span>"
                    add_notification(
                        domain,
                        "Bid Registration",
                        content,
                        user_id=broker_detail.id,
                        added_by=broker_detail.id,
                        notification_for=2,
                        property_id=p_id
                    )
                # send approval notif if auto approval on
                content = "Your registration has been approved! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain,
                    "Bid Registration",
                    content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    property_id=p_id
                )

            except Exception as e:
                pass
            # -----------------End Email------------
            return Response(response.parsejson("Registration Successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))