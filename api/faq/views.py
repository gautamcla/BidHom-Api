# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.faq.models import *
from api.faq.serializers import *
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


class SuperAdminAddFaqView(APIView):
    """
    Super admin add/update faq
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            faq_id = None
            if "faq_id" in data and data['faq_id'] != "":
                faq_id = int(data['faq_id'])
                faq_id = Faq.objects.filter(id=faq_id).first()
                if faq_id is None:
                    return Response(response.parsejson("Faq not exist.", "", status=403))

            domain = None
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])

            if "added_by" in data and data['added_by'] != "":
                added_by = int(data['added_by'])
                user = Users.objects.filter(id=added_by, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("added_by is required", "", status=403))

            if "question" in data and data['question'] != "":
                question = data['question']
            else:
                return Response(response.parsejson("question is required", "", status=403))

            if "answer" in data and data['answer'] != "":
                answer = data['answer']
            else:
                return Response(response.parsejson("answer is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            serializer = FaqSerializer(faq_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Faq added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminFaqDetailApiView(APIView):
    """
    Super admin contact us detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "faq_id" in data and data['faq_id'] != "":
                faq_id = int(data['faq_id'])
            else:
                return Response(response.parsejson("faq_id is required", "", status=403))

            faq = Faq.objects.get(id=faq_id)
            serializer = SuperAdminFaqDetailSerializer(faq)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminFaqListingApiView(APIView):
    """
    Super admin add/update faq
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

            faq = Faq.objects
            if "site_id" in data and type(data['site_id']) == list and len(data['site_id']) > 0:
                site_id = data['site_id']
                faq = faq.filter(domain__in=site_id)
            else:
                faq = faq.filter(domain__isnull=True)

            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                status = data['status']
                faq = faq.filter(status__in=status)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    faq = faq.filter(Q(id=search))
                else:
                    faq = faq.filter(Q(question__icontains=search) | Q(answer__icontains=search) | Q(domain__domain_name__icontains=search))
            total = faq.count()
            faq = faq.order_by("-id").only("id")[offset: limit]
            serializer = SuperAdminFaqListingSerializer(faq, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainAddFaqView(APIView):
    """
    Subdomain admin add/update faq
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            faq_id = None
            if "faq_id" in data and data['faq_id'] != "":
                faq_id = int(data['faq_id'])
                faq_id = Faq.objects.filter(id=faq_id).first()
                if faq_id is None:
                    return Response(response.parsejson("Faq not exist.", "", status=403))

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = int(data['added_by'])
                user = Users.objects.filter(id=added_by, site=domain, user_type=2, status=1).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=added_by, is_agent=1, status=1, user__user_type=2).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to add/update.", "", status=403))
            else:
                return Response(response.parsejson("added_by is required", "", status=403))

            if "question" in data and data['question'] != "":
                question = data['question']
            else:
                return Response(response.parsejson("question is required", "", status=403))

            if "answer" in data and data['answer'] != "":
                answer = data['answer']
            else:
                return Response(response.parsejson("answer is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                user_type = 1
                # return Response(response.parsejson("user_type is required", "", status=403))

            serializer = FaqSerializer(faq_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Faq added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainFaqDetailApiView(APIView):
    """
    Subdomain admin contact us detail
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

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=site_id, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, user__status=1, user__user_type=2).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "faq_id" in data and data['faq_id'] != "":
                faq_id = int(data['faq_id'])
            else:
                return Response(response.parsejson("faq_id is required", "", status=403))

            faq = Faq.objects.get(id=faq_id, domain=site_id)
            serializer = SubdomainFaqDetailSerializer(faq)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainFaqListingApiView(APIView):
    """
    Subdomain admin add/update faq
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

            if "user" in data and data['user'] != "":
                user_id = data['user']
                user = Users.objects.filter(id=user_id, status=1, site=site_id, user_type=2).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, user__status=1, user__user_type=2).first()
                    if network_user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            faq = Faq.objects.filter(domain=site_id).exclude(status=5)
            if "status" in data and data['status'] != "":
                status = data['status']
                faq = faq.filter(status=status)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    faq = faq.filter(Q(id=search))
                else:
                    faq = faq.filter(Q(question__icontains=search) | Q(answer__icontains=search) | Q(domain__domain_name__icontains=search))
            total = faq.count()
            faq = faq.order_by("-id").only("id")[offset: limit]
            serializer = SubdomainFaqListingSerializer(faq, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FaqListingApiView(APIView):
    """
    Faq listing
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

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

            faq = Faq.objects.filter((Q(domain=site_id) | Q(domain__isnull=True)) & Q(status=1))
            if "faq_type" in data and data['faq_type'] != "":
                faq = faq.filter(user_type=int(data['faq_type']))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    faq = faq.filter(Q(id=search))
                else:
                    faq = faq.filter(Q(question__icontains=search) | Q(answer__icontains=search) | Q(domain__domain_name__icontains=search))
            total = faq.count()
            faq = faq.order_by("-id").only("id")
            serializer = FaqListingSerializer(faq, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


