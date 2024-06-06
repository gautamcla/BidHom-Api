# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.users.models import *
from api.network.serializers import *
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


class AdminActiveDomainApiView(APIView):
    """
    Admin active domain listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            network_domain = NetworkDomain.objects.filter(is_active=1).order_by("-id")
            serializer = AdminActiveDomainSerializer(network_domain, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminActiveNetworkAgentApiView(APIView):
    """
    Admin active network agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id']:
                if type(data['site_id']) == list and len(data['site_id']) > 0:
                    site_id = data["site_id"]
                else:
                    site_id = [int(data['site_id'])]
                network = NetworkDomain.objects.filter(id__in=site_id, is_active=1)
                if not network:
                    return Response(response.parsejson("Site's not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id[] is required", "", status=403))

            users_one = Users.objects.filter(site__in=site_id, status=1)
            users_two = Users.objects.filter(network_user__domain__in=site_id, network_user__is_agent=1, user_type=2, status=1)
            users = users_one.union(users_two).order_by('-id')
            serializer = AdminActiveNetworkAgentSerializer(users, many=True)
            
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


