# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.users.models import *
from api.home.serializers import *
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


class DetailApiView(APIView):
    """
    Home detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            user_id = None
            if "user_id" in data and data['user_id'] is not None and data['user_id'] != 'None' and data['user_id'] != "":
                user_id = int(data['user_id'])

            if "site_id" in data and data['site_id'] != "":
                site_id = data['site_id']
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required", "", status=403))
            network_domain = NetworkDomain.objects.get(id=site_id, is_active=1)
            serializer = DetailSerializer(network_domain, context=user_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


