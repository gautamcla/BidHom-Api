# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
import datetime
from django.utils import timezone
from api.advertisement.serializers import *
from api.packages.globalfunction import *
from django.db import transaction
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.db.models import F
from django.db.models import Q
from django.db.models import Count
from django.conf import settings


class AddAdvertisementApiView(APIView):
    """
    Add/Update advertisement
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            advertisement_id = None
            if "advertisement_id" in data and data['advertisement_id'] != "":
                advertisement_id = int(data['advertisement_id'])
                advertisement_id = Advertisement.objects.filter(id=advertisement_id).first()
                if advertisement_id is None:
                    return Response(response.parsejson("Advertisement not exist.", "", status=403))

            domain = None
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])

            if "company_name" in data and data['company_name'] != "":
                company_name = data['company_name']
            else:
                return Response(response.parsejson("company_name is required.", "", status=403))

            if "url" in data and data['url'] != "":
                url = data['url']
            else:
                return Response(response.parsejson("url is required.", "", status=403))

            if "image" in data and data['image'] != "":
                image = int(data['image'])
            else:
                return Response(response.parsejson("image is required.", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = data['added_by']
                data['updated_by'] = data['added_by']
            else:
                return Response(response.parsejson("added_by is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            print(data)
            serializer = AdvertisementSerializer(advertisement_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Advertisement added/updated successfully.", "", status=201))
        except Exception as exp:
            print(exp)
            return Response(response.parsejson(str(exp), exp, status=403))


class TrackAdvertisementApiView(APIView):
    """
    Track advertisement
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "advertisement" in data and data['advertisement'] != "":
                advertisement = int(data['advertisement'])
                advertisement_id = Advertisement.objects.filter(id=advertisement).first()
                if advertisement_id is None:
                    return Response(response.parsejson("Advertisement not exist.", "", status=403))
            else:
                return Response(response.parsejson("advertisement is required.", "", status=403))

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=domain, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=domain).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
                property_data = PropertyListing.objects.filter(id=property_id, domain=domain).first()
                if property_data is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
            else:
                return Response(response.parsejson("property is required.", "", status=403))

            serializer = TrackAdvertisementSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Add data successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminAdvertisementListingApiView(APIView):
    """
    Super admin advertisement listing
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
            domain = None
            if "domain" in data and type(data['domain']) == list and len(data['domain']) > 0:
                domain = data['domain']
            advertisement = Advertisement.objects

            if domain is not None and len(domain) > 0:
                advertisement = advertisement.filter(domain__in=domain)
            
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                advertisement = advertisement.filter(status__in=data["status"])

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    # advertisement = advertisement.annotate(add_view_count=Count('track_advertisement__id')).filter(Q(id=search) | Q(add_view_count__icontains=search))
                    advertisement = advertisement.annotate(add_view_count=Count('track_advertisement__id')).filter(Q(add_view_count__icontains=search))
                else:
                    advertisement = advertisement.annotate(add_view_count=Count('track_advertisement__id')).filter(Q(domain__domain_name__icontains=search) | Q(company_name__icontains=search) | Q(url__icontains=search) | Q(status__status_name__icontains=search) | Q(add_view_count__icontains=search))

            total = advertisement.count()
            advertisement = advertisement.order_by("-id").only("id")[offset: limit]
            serializer = SuperAdminAdvertisementListingSerializer(advertisement, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminAdvertisementDetailApiView(APIView):
    """
    Super admin advertisement detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            domain = None
            if "advertisement_id" in data and data['advertisement_id'] != "":
                advertisement_id = int(data['advertisement_id'])
            else:
                return Response(response.parsejson("advertisement_id is required", "", status=403))

            advertisement = Advertisement.objects.get(id=advertisement_id)
            serializer = SuperAdminAdvertisementDetailSerializer(advertisement)
            all_data = {
                "data": serializer.data
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))




