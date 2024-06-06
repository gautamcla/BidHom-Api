# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.settings.models import *
from api.contact.models import *
import datetime
from django.utils import timezone
from api.settings.serializers import *
from api.packages.globalfunction import *
from django.db import transaction
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.db.models import F
from django.db.models import Q, Count, Sum


class GetStateApiView(APIView):
    """
    Get State List
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "country_id" in data and data['country_id'] != "":
                country_id = int(data['country_id'])
            else:
                country_id = 1
            state = LookupState.objects.filter(country=country_id, is_active=1).order_by("state_name").values('id', 'iso_name', 'state_name')
            return Response(response.parsejson("Fetch Daa.", state, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetCountryApiView(APIView):
    """
    Get Country List
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            country = LookupCountry.objects.filter(is_active=1).order_by("country_name").values('id', 'iso_name', 'country_name', 'alpha2_code')
            return Response(response.parsejson("Fetch Daa.", country, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddThemeApiView(APIView):
    """
    Add theme
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            theme_id = None
            if "theme_id" in data and data['theme_id'] != "":
                theme_id = data['theme_id']
                theme_id = ThemesAvailable.objects.filter(id=theme_id).first()
            if "theme_name" in data and data['theme_name'] != "":
                theme_name = data['theme_name'].strip()
                theme = ThemesAvailable.objects.filter(theme_name=theme_name).first()
                if theme_id:
                    theme = ThemesAvailable.objects.filter(theme_name=theme_name).exclude(id=theme_id.id).first()
                if theme:
                    return Response(response.parsejson("Theme already exist.", "", status=403))
            else:
                # Translators: This message appears when theme name is empty
                return Response(response.parsejson("Theme Name is required", "", status=403))

            if "theme_dir" in data and data['theme_dir'] != "":
                theme_dir = data['theme_dir'].strip()
                name_exist = ThemesAvailable.objects.filter(theme_dir=theme_dir).first()
                if theme_id:
                    name_exist = ThemesAvailable.objects.filter(theme_dir=theme_dir).exclude(id=theme_id.id).first()
                if name_exist:
                    return Response(response.parsejson("Theme Directory already exist", "", status=403))
            else:
                # Translators: This message appears when theme_dir is empty
                return Response(response.parsejson("Theme Directory is required", "", status=403))

            serializer = ThemesAvailableSerializer(data=data)
            if theme_id:
                serializer = ThemesAvailableSerializer(theme_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Theme saved/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ThemeStatusChangeApiView(APIView):
    """
    Delete theme
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "theme_id" in data and data['theme_id'] != "":
                theme_id = int(data['theme_id'])
            else:
                # Translators: This message appears when theme_id is empty
                return Response(response.parsejson("theme_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                # Translators: This message appears when status is empty
                return Response(response.parsejson("status is required", "", status=403))
            ThemesAvailable.objects.filter(id=theme_id).update(is_active=status)
            return Response(response.parsejson("Status changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminThemeListingApiView(APIView):
    """
    Admin theme listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            themes_available = ThemesAvailable.objects.filter(id__gte=1)
            serializer = ThemesAvailableSerializer(themes_available, many=True)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ThemeListingApiView(APIView):
    """
    Theme listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            themes_available = ThemesAvailable.objects.filter(is_active=1)
            serializer = ThemesAvailableSerializer(themes_available, many=True)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserThemeListingApiView(APIView):
    """
    Admin User Theme listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            themes_available = ThemesAvailable.objects.filter(is_active=1).order_by("id").values('id', 'theme_name', 'is_default')
            return Response(response.parsejson("Fetch Data.", themes_available, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminThemeDetailApiView(APIView):
    """
    Theme Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "theme_id" in data and data['theme_id'] != "":
                theme_id = data['theme_id']
            else:
                return Response(response.parsejson("theme_id is required.", "", status=403))

            themes_available = ThemesAvailable.objects.get(id=theme_id)
            serializer = AdminThemeDetailSerializer(themes_available)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), "", status=403))


class AddSubscriptionApiView(APIView):
    """
    Add theme
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            subscription_id = None
            if "subscription_id" in data and data['subscription_id'] != "":
                subscription_id = data['subscription_id']

            if "plan_name" in data and data['plan_name'] != "":
                plan_name = data['plan_name'].strip()
                subscription = SubscriptionPlan.objects.filter(plan_name=plan_name).exclude(id=subscription_id).first()
                if subscription:
                    return Response(response.parsejson("Plan already exist.", "", status=403))
            else:
                # Translators: This message appears when plan_name is empty
                return Response(response.parsejson("plan_name is required", "", status=403))

            if "plan_desc" in data and data['plan_desc'] != "":
                plan_desc = data['plan_desc'].strip()
            else:
                # Translators: This message appears when plan_desc is empty
                return Response(response.parsejson("plan_desc is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            with transaction.atomic():
                subscription_plan = SubscriptionPlan.objects.filter(id=subscription_id).first()
                serializer = SubscriptionPlanSerializer(subscription_plan, data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Subscription plan saved successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSubscriptionListingApiView(APIView):
    """
    Admin Subscription listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            subscription_plan = SubscriptionPlan.objects.filter(id__gte=1).exclude(is_delete=1).order_by("id")
            serializer = SubscriptionPlanListingSerializer(subscription_plan, many=True)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubscriptionListingApiView(APIView):
    """
    Subscription listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required", "", status=403))

            subscription_plan = SubscriptionPlan.objects.filter(is_active=1, plan_pricing_subscription__is_active=1).order_by("plan_pricing_subscription__cost")
            serializer = SubscriptionListingSerializer(subscription_plan, many=True, context=user_id)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserSubscriptionListingApiView(APIView):
    """
    Admin User Subscription listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            subscription_plan = SubscriptionPlan.objects.filter(is_active=1, plan_pricing_subscription__is_active=1).order_by("plan_pricing_subscription__cost").values('id', 'plan_name')
            return Response(response.parsejson("Fetch Data.", subscription_plan, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubscriptionStatusChangeApiView(APIView):
    """
    Subscription status change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "subscription_id" in data and data['subscription_id'] != "":
                subscription_id = int(data['subscription_id'])
            else:
                # Translators: This message appears when subscription_id is empty
                return Response(response.parsejson("subscription_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))
            SubscriptionPlan.objects.filter(id=subscription_id).update(is_active=is_active)
            return Response(response.parsejson("Status changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubscriptionDetailApiView(APIView):
    """
    Subscription detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "subscription_id" in data and data['subscription_id'] != "":
                subscription_id = int(data['subscription_id'])
            else:
                # Translators: This message appears when subscription_id is empty
                return Response(response.parsejson("subscription_id is required", "", status=403))

            subscription_plan = SubscriptionPlan.objects.get(id=subscription_id)
            serializer = SubscriptionDetailSerializer(subscription_plan)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddLookupObjectApiView(APIView):
    """
    AddLookupObjectApiView
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            object_id = None
            if "object_id" in data and data['object_id'] != "":
                object_id = int(data['object_id'])

            if "object_name" in data and data['object_name'] != "":
                object_name = data['object_name']
                lookup = LookupObject.objects.filter(object_name=object_name).exclude(id=object_id).first()
                if lookup:
                    return Response(response.parsejson("Object Already exist.", "", status=403))
            else:
                # Translators: This message appears when object_name is empty
                return Response(response.parsejson("object_name is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            if object_id is not None:
                lookup_object = LookupObject.objects.filter(id=object_id).first()
            else:
                lookup_object = LookupObject()

            lookup_object.is_active = is_active
            lookup_object.object_name = object_name
            lookup_object.save()
            return Response(response.parsejson("Lookup Object added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectDetailApiView(APIView):
    """
    Lookup object Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "object_id" in data and data['object_id'] != "":
                object_id = data['object_id']
            else:
                # Translators: This message appears when object_id is empty
                return Response(response.parsejson("object_id is required", "", status=403))
            lookup = LookupObject.objects.filter(id=object_id).values('id', "object_name", "is_active")
            return Response(response.parsejson("Fetch Data", lookup, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectStatusChangeApiView(APIView):
    """
    Lookup object change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "object_id" in data and data['object_id'] != "":
                object_id = data['object_id']
            else:
                # Translators: This message appears when object_id is empty
                return Response(response.parsejson("object_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            LookupObject.objects.filter(id=object_id).update(is_active=is_active)
            return Response(response.parsejson("Lookup Object changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectListingApiView(APIView):
    """
    Lookup object listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_object = LookupObject.objects.filter(id__gte=1).order_by("-id").values('id', 'object_name',
                                                                                          'is_active')
            return Response(response.parsejson("Fetch Data", lookup_object, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddLookupStatusApiView(APIView):
    """
    Add Lookup status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            status_id = None
            if "status_id" in data and data['status_id'] != "":
                status_id = data['status_id']

            if "status_name" in data and data['status_name'] != "":
                status_name = data['status_name']
                status = LookupStatus.objects.filter(status_name=status_name).exclude(id=status_id).first()
                if status:
                    return Response(response.parsejson("Status already exist.", "", status=403))
            else:
                # Translators: This message appears when status_name is empty
                return Response(response.parsejson("status_name is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            lookup_status = LookupStatus.objects.filter(id=status_id).first()
            if lookup_status is None:
                lookup_status = LookupStatus()

            lookup_status.is_active = is_active
            lookup_status.status_name = status_name
            lookup_status.save()
            return Response(response.parsejson("Lookup status added/updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupStatusChangeStatusApiView(APIView):
    """
    Lookup status change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "status_id" in data and data['status_id'] != "":
                status_id = data['status_id']
            else:
                # Translators: This message appears when status_id is empty
                return Response(response.parsejson("status_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            LookupStatus.objects.filter(id=status_id).update(is_active=is_active)
            return Response(response.parsejson("Lookup status changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminLookupStatusListingApiView(APIView):
    """
    Admin Status Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_status = LookupStatus.objects.filter(id__gte=1).order_by("-id")
            serializer = LookupStatusSerializer(lookup_status, many=True)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupStatusListingApiView(APIView):
    """
    Status Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            object_id = None
            if "object_id" in data and data['object_id'] != "":
                object_id = data['object_id']

            lookup_status = LookupStatus.objects.filter(is_active=1)
            if object_id is not None:
                lookup_status = lookup_status.filter(lookup_object_status__object=object_id,
                                                     lookup_object_status__is_active=1,
                                                     lookup_object_status__object__is_active=1)
            lookup_status = lookup_status.order_by("id")
            serializer = LookupStatusSerializer(lookup_status, many=True)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupStatusDetailApiView(APIView):
    """
    Status Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "status_id" in data and data['status_id'] != "":
                status_id = data['status_id']
            else:
                return Response(response.parsejson("status_id is required.", "", status=403))

            lookup_status = LookupStatus.objects.get(id=status_id)
            serializer = LookupStatusDetailSerializer(lookup_status)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), "", status=403))


class AddLookupObjectStatusApiView(APIView):
    """
    AddLookupObjectStatusApiView
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            status_object_id = None
            if "status_object_id" in data and data['status_object_id'] != "":
                status_object_id = int(data['status_object_id'])

            if "object_id" in data and data['object_id'] != "":
                object_id = int(data['object_id'])
            else:
                # Translators: This message appears when object_id is empty
                return Response(response.parsejson("object_id is required", "", status=403))

            if "status_id" in data and data['status_id'] != "":
                status_id = int(data['status_id'])
            else:
                # Translators: This message appears when status_id is empty
                return Response(response.parsejson("status_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))
            # --------Check value already exist---------
            lookup_object_status = LookupObjectStatus.objects.filter(object=object_id, status=status_id).exclude(id=status_object_id).first()
            if lookup_object_status is not None:
                return Response(response.parsejson("Already exist.", "", status=403))

            lookup_object_status = LookupObjectStatus.objects.filter(id=status_object_id).first()
            if lookup_object_status is None:
                lookup_object_status = LookupObjectStatus()

            lookup_object_status.is_active = is_active
            lookup_object_status.object_id = object_id
            lookup_object_status.status_id = status_id
            lookup_object_status.save()
            return Response(response.parsejson("Save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectStatusDetailApiView(APIView):
    """
    Lookup object status detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "status_object_id" in data and data['status_object_id'] != "":
                status_object_id = int(data['status_object_id'])
            else:
                # Translators: This message appears when status_object_id is empty
                return Response(response.parsejson("status_object_id is required", "", status=403))
            lookup = LookupObjectStatus.objects.filter(id=status_object_id).values('id', "object_id", "status_id", "is_active")
            return Response(response.parsejson("Fetch Data", lookup, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectChangeStatusApiView(APIView):
    """
    Lookup object change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "status_object_id" in data and data['status_object_id'] != "":
                status_object_id = int(data['status_object_id'])
            else:
                # Translators: This message appears when status_object_id is empty
                return Response(response.parsejson("status_object_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))

            LookupObjectStatus.objects.filter(id=status_object_id).update(is_active=is_active)
            return Response(response.parsejson("Changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LookupObjectStatusListingApiView(APIView):
    """
    Lookup object status listing
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

            lookup = LookupObjectStatus.objects

            # --------Filter--------
            if "object_id" in data and data['object_id'] != "":
                lookup = lookup.filter(object=data['object_id'])
            
            if "search" in data and data["search"] != "":
                search = data['search']
                if search.isdigit():
                    lookup = lookup.filter(Q(id=search))
                else:
                    lookup = lookup.filter(Q(object__object_name__icontains=search) | Q(status__status_name__icontains=search))

            total = lookup.count()
            lookup = lookup.order_by("-id").only("id")[offset: limit]
            serializer = LookupObjectStatusListingSerializer(lookup, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPlanTypeApiView(APIView):
    """
    Add/Update Plan type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            type_id = None
            if "type_id" in data and data['type_id'] != "":
                type_id = int(data['type_id'])

            if "type_name" in data and data['type_name'] != "":
                type_name = data['type_name']
                plan_type = PlanType.objects.filter(type_name=type_name).exclude(id=type_id).first()
                if plan_type:
                    return Response(response.parsejson("Plan name already exist.", "", status=403))
            else:
                return Response(response.parsejson("type_name is required.", "", status=403))

            if "duration_in_days" in data and data['duration_in_days'] != "":
                duration_in_days = int(data['duration_in_days'])
            else:
                return Response(response.parsejson("duration_in_days is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            if "benefits" in data and data['benefits'] != "":
                benefits = data['benefits']
            else:
                return Response(response.parsejson("benefits is required.", "", status=403))

            plan_type = PlanType()
            if type_id is not None:
                plan_type = PlanType.objects.filter(id=type_id).first()
            plan_type.type_name = type_name
            plan_type.duration_in_days = duration_in_days
            plan_type.is_active = is_active
            plan_type.save()
            plan_id = plan_type.id
            plan_benefits = PlanBenefits.objects.filter(plan=plan_id).first()
            if plan_benefits is None:
                plan_benefits = PlanBenefits()
                plan_benefits.plan_id = plan_id
            plan_benefits.benefits = benefits
            plan_benefits.save()
            return Response(response.parsejson("Plan type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanTypeDetailApiView(APIView):
    """
    Plan type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "type_id" in data and data['type_id'] != "":
                type_id = int(data['type_id'])
            else:
                return Response(response.parsejson("type_id is required.", "", status=403))

            plan_type = PlanType.objects.filter(id=type_id).values("id", "type_name", "duration_in_days", "is_active",
                                                                   benefits=F("plan_benefits_plan__benefits"))
            return Response(response.parsejson("Fetch Data", plan_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanTypeChangeStatusApiView(APIView):
    """
    Plan type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "type_id" in data and data['type_id'] != "":
                type_id = int(data['type_id'])
            else:
                return Response(response.parsejson("type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            plan_type = PlanType.objects.filter(id=type_id).update(is_active=is_active)
            return Response(response.parsejson("Plan type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanTypeListingApiView(APIView):
    """
    Plan type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            plan_type = PlanType.objects.filter(id__gte=1).exclude(is_delete=1).order_by("-id").values("id", "type_name", "duration_in_days", "is_active", benefits=F("plan_benefits_plan__benefits"))
            return Response(response.parsejson("Fetch Data.", plan_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddUserTypeApiView(APIView):
    """
    Add/Update User type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            user_type_id = None
            if "user_type_id" in data and data['user_type_id'] != "":
                user_type_id = int(data['user_type_id'])

            if "user_type" in data and data['user_type'] != "":
                user_type = data['user_type']
                users_type = LookupUserType.objects.filter(user_type=user_type).exclude(id=user_type_id).first()
                if users_type:
                    return Response(response.parsejson("User type name already exist.", "", status=403))
            else:
                return Response(response.parsejson("type_name is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_user_type = LookupUserType.objects.filter(id=user_type_id).first()
            if lookup_user_type is None:
                lookup_user_type = LookupUserType()
            lookup_user_type.user_type = user_type
            lookup_user_type.is_active = is_active
            lookup_user_type.save()
            return Response(response.parsejson("User type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserTypeDetailApiView(APIView):
    """
    User type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_type_id" in data and data['user_type_id'] != "":
                user_type_id = int(data['user_type_id'])
            else:
                return Response(response.parsejson("user_type_id is required.", "", status=403))

            user_type = LookupUserType.objects.filter(id=user_type_id).values("id", "user_type", "is_active")
            return Response(response.parsejson("Fetch Data", user_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserTypeChangeStatusApiView(APIView):
    """
    User type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_type_id" in data and data['user_type_id'] != "":
                user_type_id = int(data['user_type_id'])
            else:
                return Response(response.parsejson("user_type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupUserType.objects.filter(id=user_type_id).update(is_active=is_active)
            return Response(response.parsejson("User type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserTypeListingApiView(APIView):
    """
    User type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_user_type = LookupUserType.objects.filter(id__gte=1).order_by("-id").values("id", "user_type", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_user_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyTypeApiView(APIView):
    """
    Add/Update Property type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            property_type_id = None
            if "property_type_id" in data and data['property_type_id'] != "":
                property_type_id = int(data['property_type_id'])

            if "property_type" in data and data['property_type'] != "":
                property_type = data['property_type']
                lookup_property_type = LookupPropertyType.objects.filter(property_type=property_type).exclude(id=property_type_id).first()
                if lookup_property_type:
                    return Response(response.parsejson("Property Type name already exist.", "", status=403))
            else:
                return Response(response.parsejson("property_type is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_property_type = LookupPropertyType.objects.filter(id=property_type_id).first()
            if lookup_property_type is None:
                lookup_property_type = LookupPropertyType()
            lookup_property_type.property_type = property_type
            lookup_property_type.is_active = is_active
            lookup_property_type.save()
            return Response(response.parsejson("Property type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTypeDetailApiView(APIView):
    """
    Property type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_type_id" in data and data['property_type_id'] != "":
                property_type_id = int(data['property_type_id'])
            else:
                return Response(response.parsejson("property_type_id is required.", "", status=403))

            property_type = LookupPropertyType.objects.filter(id=property_type_id).values("id", "property_type", "is_active")
            return Response(response.parsejson("Fetch Data", property_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTypeChangeStatusApiView(APIView):
    """
    User type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_type_id" in data and data['property_type_id'] != "":
                property_type_id = int(data['property_type_id'])
            else:
                return Response(response.parsejson("property_type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupPropertyType.objects.filter(id=property_type_id).update(is_active=is_active)
            return Response(response.parsejson("Property type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTypeListingApiView(APIView):
    """
    User type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_user_type = LookupPropertyType.objects.filter(id__gte=1).order_by("-id").values("id", "property_type", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_user_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddAuctionTypeApiView(APIView):
    """
    Add/Update Auction type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            auction_type_id = None
            if "auction_type_id" in data and data['auction_type_id'] != "":
                auction_type_id = int(data['auction_type_id'])

            if "auction_type" in data and data['auction_type'] != "":
                auction_type = data['auction_type']
                lookup_auction_type = LookupAuctionType.objects.filter(auction_type=auction_type).exclude(id=auction_type_id).first()
                if lookup_auction_type:
                    return Response(response.parsejson("Auction Type name already exist.", "", status=403))
            else:
                return Response(response.parsejson("auction_type is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_auction_type = LookupAuctionType.objects.filter(id=auction_type_id).first()
            if lookup_auction_type is None:
                lookup_auction_type = LookupAuctionType()
            lookup_auction_type.auction_type = auction_type
            lookup_auction_type.is_active = is_active
            lookup_auction_type.save()
            return Response(response.parsejson("Auction type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionTypeDetailApiView(APIView):
    """
    Auction type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "auction_type_id" in data and data['auction_type_id'] != "":
                auction_type_id = int(data['auction_type_id'])
            else:
                return Response(response.parsejson("auction_type_id is required.", "", status=403))

            auction_type = LookupAuctionType.objects.filter(id=auction_type_id).values("id", "auction_type", "is_active")
            return Response(response.parsejson("Fetch Data", auction_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionTypeChangeStatusApiView(APIView):
    """
    Auction type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "auction_type_id" in data and data['auction_type_id'] != "":
                auction_type_id = int(data['auction_type_id'])
            else:
                return Response(response.parsejson("auction_type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupAuctionType.objects.filter(id=auction_type_id).update(is_active=is_active)
            return Response(response.parsejson("Auction type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionTypeListingApiView(APIView):
    """
    Auction type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_auction_type = LookupAuctionType.objects.filter(id__gte=1).order_by("-id").values("id", "auction_type", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_auction_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainAuctionTypeApiView(APIView):
    """
    Subdomain auction listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_auction_type = LookupAuctionType.objects.filter(is_active=1).order_by("auction_type").values("id", "auction_type")
            return Response(response.parsejson("Fetch Data.", lookup_auction_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddDocumentsTypeApiView(APIView):
    """
    Add/Update Document type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            documents_type_id = None
            if "documents_type_id" in data and data['documents_type_id'] != "":
                documents_type_id = int(data['documents_type_id'])

            if "document_name" in data and data['document_name'] != "":
                document_name = data['document_name']
                lookup_documents = LookupDocuments.objects.filter(document_name=document_name).exclude(id=documents_type_id).first()
                if lookup_documents:
                    return Response(response.parsejson("Document Type name already exist.", "", status=403))
            else:
                return Response(response.parsejson("document_name is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_documents = LookupDocuments.objects.filter(id=documents_type_id).first()
            if lookup_documents is None:
                lookup_documents = LookupDocuments()
            lookup_documents.document_name = document_name
            lookup_documents.is_active = is_active
            lookup_documents.save()
            return Response(response.parsejson("Document type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DocumentsTypeDetailApiView(APIView):
    """
    Documents type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "documents_type_id" in data and data['documents_type_id'] != "":
                documents_type_id = int(data['documents_type_id'])
            else:
                return Response(response.parsejson("documents_type_id is required.", "", status=403))

            documents_type = LookupDocuments.objects.filter(id=documents_type_id).values("id", "document_name", "is_active")
            return Response(response.parsejson("Fetch Data", documents_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DocumentsTypeChangeStatusApiView(APIView):
    """
    Documents type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "documents_type_id" in data and data['documents_type_id'] != "":
                documents_type_id = int(data['documents_type_id'])
            else:
                return Response(response.parsejson("documents_type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupDocuments.objects.filter(id=documents_type_id).update(is_active=is_active)
            return Response(response.parsejson("Documents type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DocumentsTypeListingApiView(APIView):
    """
    Documents type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_documents = LookupDocuments.objects.filter(id__gte=1).order_by("-id").values("id", "document_name", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_documents, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddAddressTypeApiView(APIView):
    """
    Add/Update Address type
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            address_type_id = None
            if "address_type_id" in data and data['address_type_id'] != "":
                address_type_id = int(data['address_type_id'])

            if "address_type" in data and data['address_type'] != "":
                address_type = data['address_type']
                lookup_address_type = LookupAddressType.objects.filter(address_type=address_type).exclude(id=address_type_id).first()
                if lookup_address_type:
                    return Response(response.parsejson("Address Type already exist.", "", status=403))
            else:
                return Response(response.parsejson("address_type is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_address_type = LookupAddressType.objects.filter(id=address_type_id).first()
            if lookup_address_type is None:
                lookup_address_type = LookupAddressType()
            lookup_address_type.address_type = address_type
            lookup_address_type.is_active = is_active
            lookup_address_type.save()
            return Response(response.parsejson("Address type added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddressTypeDetailApiView(APIView):
    """
    Address type detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "address_type_id" in data and data['address_type_id'] != "":
                address_type_id = int(data['address_type_id'])
            else:
                return Response(response.parsejson("address_type_id is required.", "", status=403))

            address_type = LookupAddressType.objects.filter(id=address_type_id).values("id", "address_type", "is_active")
            return Response(response.parsejson("Fetch Data", address_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddressTypeChangeStatusApiView(APIView):
    """
    Address type change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "address_type_id" in data and data['address_type_id'] != "":
                address_type_id = int(data['address_type_id'])
            else:
                return Response(response.parsejson("address_type_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupAddressType.objects.filter(id=address_type_id).update(is_active=is_active)
            return Response(response.parsejson("Address type status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddressTypeListingApiView(APIView):
    """
    Address type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            address_type = LookupAddressType.objects.filter(id__gte=1).order_by("-id").values("id", "address_type", "is_active")
            return Response(response.parsejson("Fetch Data.", address_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddUploadStepApiView(APIView):
    """
    Add/Update Upload step
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            upload_step_id = None
            if "upload_step_id" in data and data['upload_step_id'] != "":
                upload_step_id = int(data['upload_step_id'])

            if "uploads_name" in data and data['uploads_name'] != "":
                uploads_name = data['uploads_name']
                upload_step = LookupUploadStep.objects.filter(uploads_name=uploads_name).exclude(id=upload_step_id).first()
                if upload_step:
                    return Response(response.parsejson("Upload step already exist.", "", status=403))
            else:
                return Response(response.parsejson("uploads_name is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            upload_step = LookupUploadStep.objects.filter(id=upload_step_id).first()
            if upload_step is None:
                upload_step = LookupUploadStep()
            upload_step.uploads_name = uploads_name
            upload_step.is_active = is_active
            upload_step.save()
            return Response(response.parsejson("Upload Step added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UploadStepDetailApiView(APIView):
    """
    Upload Step detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "upload_step_id" in data and data['upload_step_id'] != "":
                upload_step_id = int(data['upload_step_id'])
            else:
                return Response(response.parsejson("upload_step_id is required.", "", status=403))

            upload_step = LookupUploadStep.objects.filter(id=upload_step_id).values("id", "uploads_name", "is_active")
            return Response(response.parsejson("Fetch Data", upload_step, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UploadStepChangeStatusApiView(APIView):
    """
    Upload Step change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "upload_step_id" in data and data['upload_step_id'] != "":
                upload_step_id = int(data['upload_step_id'])
            else:
                return Response(response.parsejson("upload_step_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupUploadStep.objects.filter(id=upload_step_id).update(is_active=is_active)
            return Response(response.parsejson("Upload Step status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UploadStepListingApiView(APIView):
    """
    Upload Step type listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            upload_step = LookupUploadStep.objects.filter(id__gte=1).order_by("-id").values("id", "uploads_name", "is_active")
            return Response(response.parsejson("Fetch Data.", upload_step, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddEventApiView(APIView):
    """
    Add/Update Event
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            event_id = None
            if "event_id" in data and data['event_id'] != "":
                event_id = int(data['event_id'])

            if "event_name" in data and data['event_name'] != "":
                event_name = data['event_name']
                lookup_event = LookupEvent.objects.filter(event_name=event_name).exclude(id=event_id).first()
                if lookup_event:
                    return Response(response.parsejson("Event already exist.", "", status=403))
            else:
                return Response(response.parsejson("event_name is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            if "slug" in data and data['slug'] != "":
                slug = data['slug']
                event_slug = LookupEvent.objects.filter(slug=slug).exclude(id=event_id).first()
                if event_slug is not None:
                    return Response(response.parsejson("slug already exist.", "", status=403))
            else:
                return Response(response.parsejson("slug is required.", "", status=403))

            lookup_event = LookupEvent.objects.filter(id=event_id).first()
            if lookup_event is None:
                lookup_event = LookupEvent()
            lookup_event.event_name = event_name
            lookup_event.slug = slug
            lookup_event.is_active = is_active
            lookup_event.save()
            return Response(response.parsejson("Event added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EventDetailApiView(APIView):
    """
    Event detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "event_id" in data and data['event_id'] != "":
                event_id = int(data['event_id'])
            else:
                return Response(response.parsejson("event_id is required.", "", status=403))

            lookup_event = LookupEvent.objects.filter(id=event_id).values("id", "event_name", "is_active")
            return Response(response.parsejson("Fetch Data", lookup_event, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EventChangeStatusApiView(APIView):
    """
    Event change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "event_id" in data and data['event_id'] != "":
                event_id = int(data['event_id'])
            else:
                return Response(response.parsejson("event_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupEvent.objects.filter(id=event_id).update(is_active=is_active)
            return Response(response.parsejson("Event status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EventListingApiView(APIView):
    """
    Event listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_event = LookupEvent.objects.filter(id__gte=1).order_by("-id").values("id", "event_name", "slug", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_event, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddSiteSettingApiView(APIView):
    """
    Add/Update Site Settings
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            setting_id = None
            if "setting_id" in data and data['setting_id'] != "":
                setting_id = int(data['setting_id'])

            if "settings_name" in data and data['settings_name'] != "":
                settings_name = data['settings_name']
                site_settings = SiteSetting.objects.filter(settings_name=settings_name).exclude(id=setting_id).first()
                if site_settings:
                    return Response(response.parsejson("Setting Name already exist.", "", status=403))
            else:
                return Response(response.parsejson("settings_name is required.", "", status=403))

            if "setting_value" in data and data['setting_value'] != "":
                setting_value = data['setting_value']
            else:
                return Response(response.parsejson("setting_value is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            site_settings = SiteSetting.objects.filter(id=setting_id).first()
            if site_settings is None:
                site_settings = SiteSetting()
            site_settings.settings_name = settings_name
            site_settings.setting_value = setting_value
            site_settings.is_active = is_active
            site_settings.save()
            return Response(response.parsejson("Setting added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SiteSettingDetailApiView(APIView):
    """
    Site Setting detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "setting_id" in data and data['setting_id'] != "":
                setting_id = int(data['setting_id'])
            else:
                return Response(response.parsejson("setting_id is required.", "", status=403))

            site_setting = SiteSetting.objects.filter(id=setting_id).values("id", "settings_name", "setting_value", "is_active")
            return Response(response.parsejson("Fetch Data", site_setting, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SiteSettingChangeStatusApiView(APIView):
    """
    Site Setting change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "setting_id" in data and data['setting_id'] != "":
                setting_id = int(data['setting_id'])
            else:
                return Response(response.parsejson("setting_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            SiteSetting.objects.filter(id=setting_id).update(is_active=is_active)
            return Response(response.parsejson("Site Setting status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SiteSettingListingApiView(APIView):
    """
    Site Setting listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            site_setting = SiteSetting.objects.filter(id__gte=1).order_by("-id").values("id", "settings_name",
                                                                                        "setting_value", "is_active")
            return Response(response.parsejson("Fetch Data.", site_setting, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPermissionApiView(APIView):
    """
    Add/Update Permission
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            permission_id = None
            if "permission_id" in data and data['permission_id'] != "":
                permission_id = int(data['permission_id'])

            if "name" in data and data['name'] != "":
                name = data['name']
                lookup_permission = LookupPermission.objects.filter(name=name).exclude(id=permission_id).first()
                if lookup_permission:
                    return Response(response.parsejson("Permission already exist.", "", status=403))
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            if "permission_type" in data and data['permission_type'] != "":
                permission_type = int(data['permission_type'])
            else:
                return Response(response.parsejson("permission_type is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            lookup_permission = LookupPermission.objects.filter(id=permission_id).first()
            if lookup_permission is None:
                lookup_permission = LookupPermission()
            lookup_permission.name = name
            lookup_permission.permission_type = permission_type
            lookup_permission.is_active = is_active
            lookup_permission.save()
            return Response(response.parsejson("Permission added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PermissionDetailApiView(APIView):
    """
    Permission detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "permission_id" in data and data['permission_id'] != "":
                permission_id = int(data['permission_id'])
            else:
                return Response(response.parsejson("permission_id is required.", "", status=403))

            lookup_permission = LookupPermission.objects.filter(id=permission_id).values("id", "name", "permission_type", "is_active")
            return Response(response.parsejson("Fetch Data", lookup_permission, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PermissionChangeStatusApiView(APIView):
    """
    Permission change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "permission_id" in data and data['permission_id'] != "":
                permission_id = int(data['permission_id'])
            else:
                return Response(response.parsejson("permission_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupPermission.objects.filter(id=permission_id).update(is_active=is_active)
            return Response(response.parsejson("Permission status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PermissionListingApiView(APIView):
    """
    Permission listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_permission = LookupPermission.objects.filter(id__gte=1).order_by("-id").values("id", "name", "permission_type", "is_active")
            return Response(response.parsejson("Fetch Data.", lookup_permission, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AgentPermissionListingApiView(APIView):
    """
    Permission listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_permission = LookupPermission.objects.filter(is_active=1).order_by("-id").values("id", "name")
            return Response(response.parsejson("Fetch Data.", lookup_permission, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyFeaturesApiView(APIView):
    """
    Add/Update property params
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
            data = request.data
            feature_id = None
            if "feature_id" in data and data['feature_id'] != "":
                feature_id = int(data['feature_id'])

            if "feature_type" in data and data['feature_type'] != "":
                feature_type = data['feature_type'].strip()
                feature_table = features_table[feature_type]
            else:
                return Response(response.parsejson("feature_type is required.", "", status=403))

            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            else:
                return Response(response.parsejson("asset_id is required.", "", status=403))

            if "name" in data and data['name'] != "":
                name = data['name'].strip()
                if feature_type == "property_type":
                    check_name = feature_table.objects.filter(property_type=name, asset=asset_id).exclude(id=feature_id).first()
                else:
                    check_name = feature_table.objects.filter(name=name, asset=asset_id).exclude(id=feature_id).first()
                if check_name is not None:
                    return Response(response.parsejson("name is already exist.", "", status=403))
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))
            feature = feature_table.objects.filter(id=feature_id).first()
            if feature is None:
                feature = feature_table()
            if feature_type == "property_type":
                feature.property_type = name
            else:
                feature.name = name
            feature.asset_id = asset_id
            feature.is_active = is_active
            feature.save()
            return Response(response.parsejson("Data added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFeaturesDetailApiView(APIView):
    """
    Property features detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
            data = request.data
            if "feature_id" in data and data['feature_id'] != "":
                feature_id = int(data['feature_id'])
            else:
                return Response(response.parsejson("feature_id is required.", "", status=403))

            if "feature_type" in data and data['feature_type'] != "":
                feature_type = data['feature_type']
                feature_table = features_table['feature_type']
            else:
                return Response(response.parsejson("feature_type is required.", "", status=403))
            if feature_type == "property_type":
                feature = feature_table.objects.filter(id=feature_id).values("id", "asset_id", "is_active", name=F("property_type"))
            else:
                feature = feature_table.objects.filter(id=feature_id).values("id", "asset_id", "name", "is_active")
            return Response(response.parsejson("Fetch data.", feature, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFeaturesChangeStatusApiView(APIView):
    """
    Property features change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
            data = request.data
            if "feature_id" in data and data['feature_id'] != "":
                feature_id = int(data['feature_id'])
            else:
                return Response(response.parsejson("feature_id is required.", "", status=403))

            if "feature_type" in data and data['feature_type'] != "":
                feature_type = data['feature_type']
                feature_table = features_table[feature_type]
            else:
                return Response(response.parsejson("feature_type is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = data['is_active']
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            feature_table.objects.filter(id=feature_id).update(is_active=is_active)
            return Response(response.parsejson("Status change successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFeaturesListingApiView(APIView):
    """
    Property features listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
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

            all_data = None
            if "all" in data and data['all'] != "":
                all_data = data['all']

            if "feature_type" in data and data['feature_type'] != "":
                feature_type = data['feature_type']
                feature_table = features_table[feature_type]
            else:
                return Response(response.parsejson("feature_type is required.", "", status=403))
            feature = feature_table.objects
            # ---------------------------Asset----------------------
            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                feature = feature.filter(asset=asset_id)
            # ---------------------------Search---------------------
            if "search" in data and data["search"] != "":
                search = data['search']
                if search.isdigit():
                    feature = feature.filter(Q(id=search))
                else:
                    if feature_type == "property_type":
                        feature = feature.filter(Q(property_type__icontains=search) | Q(asset__name__icontains=search))
                    else:
                        feature = feature.filter(Q(name__icontains=search) | Q(asset__name__icontains=search))
            if feature_type == "property_type":
                total = feature.count()
                feature = feature.order_by("-id").values("id", "is_active", "asset_id", name=F("property_type"), asset_name=F("asset__name"))
                if all_data is None or not all_data:
                    feature = feature[offset: limit]
            else:
                total = feature.count()
                feature = feature.order_by("-id").values("id", "name", "asset_id", "is_active", asset_name=F("asset__name"))
                if all_data is None or not all_data:
                    feature = feature[offset: limit]
            all_data = {"data": feature, "total": total}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyAssetListingApiView(APIView):
    """
    Property asset listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset = LookupPropertyAsset.objects.filter(is_active=1).order_by("-id").values("id", "name")
            return Response(response.parsejson("Data fetch.", asset, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TimezoneListingApiView(APIView):
    """
    Timezone listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_timezone = LookupTimezone.objects.filter(is_active=1).order_by("id").values("id", name=F("timezone"))
            return Response(response.parsejson("Data fetch.", lookup_timezone, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminTimezoneListingApiView(APIView):
    """
    Admin timezone listing
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

            lookup_timezone = LookupTimezone.objects
            if "search" in data and data["search"] != "":
                search = data['search']
                if search.isdigit():
                    lookup_timezone = lookup_timezone.filter(Q(id=search) | Q(offset=search) | Q(offset_dst=search))
                else:
                    lookup_timezone = lookup_timezone.filter(Q(timezone__icontains=search) | Q(offset=search) | Q(offset_dst=search))

            total = lookup_timezone.count()
            lookup_timezone = lookup_timezone.order_by("-id").only("id")[offset:limit]
            serializer = AdminTimezoneListingSerializer(lookup_timezone, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Data fetch.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminTimezoneChangeStatusApiView(APIView):
    """
    Admin timezone listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "timezone_id" in data and data['timezone_id'] != "":
                timezone_id = int(data['timezone_id'])
            else:
                return Response(response.parsejson("timezone_id is required.", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                return Response(response.parsejson("is_active is required.", "", status=403))

            LookupTimezone.objects.filter(id=timezone_id).update(is_active=is_active)
            return Response(response.parsejson("Status successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPlanPricingApiView(APIView):
    """
    Add plan pricing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            plan_price_id = None
            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = data['plan_price_id']

            if "subscription_id" in data and data['subscription_id'] != "":
                subscription_id = int(data['subscription_id'])
                data['subscription'] = subscription_id
            else:
                # Translators: This message appears when subscription_id is empty
                return Response(response.parsejson("subscription_id is required", "", status=403))

            if "plan_type_id" in data and data['plan_type_id'] != "":
                plan_type_id = int(data['plan_type_id'])
                data['plan_type'] = plan_type_id
            else:
                # Translators: This message appears when plan_type_id is empty
                return Response(response.parsejson("plan_type_id is required", "", status=403))

            if "cost" in data and data['cost'] != "":
                cost = float(data['cost'])
            else:
                # Translators: This message appears when cost is empty
                return Response(response.parsejson("cost is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))
            # ---------------Check data-----------
            pricing = PlanPricing.objects.filter(subscription=subscription_id, plan_type=plan_type_id).exclude(id=plan_price_id).first()
            if pricing is not None:
                return Response(response.parsejson("Already exist.", "", status=403))

            with transaction.atomic():
                plan_price = PlanPricing.objects.filter(id=plan_price_id).first()
                serializer = PlanPricingSerializer(plan_price, data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Plan price saved successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPlanPricingListingApiView(APIView):
    """
    Admin plan pricing listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            pricing = PlanPricing.objects.exclude(is_delete=1).order_by("-id").only("id")
            serializer = AdminPlanPricingListingSerializer(pricing, many=True)
            return Response(response.parsejson("Fetch data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanPricingStatusChangeApiView(APIView):
    """
    Admin plan pricing change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
            else:
                # Translators: This message appears when plan_price_id is empty
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
            else:
                # Translators: This message appears when is_active is empty
                return Response(response.parsejson("is_active is required", "", status=403))
            PlanPricing.objects.filter(id=plan_price_id).update(is_active=is_active)
            return Response(response.parsejson("Status change successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanPricingDetailApiView(APIView):
    """
    Plan pricing detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
            else:
                # Translators: This message appears when plan_price_id is empty
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            price = PlanPricing.objects.get(id=plan_price_id)
            serializer = PlanPricingDetailSerializer(price)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubscriptionListApiView(APIView):
    """
    Subscription list
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            subscription = SubscriptionPlan.objects.filter(is_active=1, is_free=0).exclude(is_delete=1).order_by("-id").values("id", "plan_name")
            return Response(response.parsejson("Fetch data.", subscription, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanTypeListApiView(APIView):
    """
    Plan type list
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            plan_type = PlanType.objects.filter(is_active=1).exclude(is_delete=1).order_by("-id").values("id", "type_name")
            return Response(response.parsejson("Fetch data.", plan_type, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChatCountApiView(APIView):
    """
    Chat count
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

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user_type = "broker"
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    user_type = "agent"
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__status=1, network_user__is_agent=1).first()
                    if users is None:
                        user_type = "customer"
                        users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=site_id).first()
                        if users is None:
                            return Response(response.parsejson("User not exist", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            message_count = {}
            message_count['user_msg_cnt'] = Chat.objects.filter(master__domain=site_id, master__buyer=user_id, receiver=user_id, status=1, is_read=0).count()
            if user_type == "broker":
                # agent_list = NetworkUser.objects.filter(domain=site_id, is_agent=1, status=1).values("user_id")
                agent_list = MasterChat.objects.filter(domain=site_id, status=1).values("seller_id")
                agent_list = [i['seller_id'] for i in agent_list]
                agent_broker_list = agent_list.copy()
                agent_broker_list.append(user_id)
                agent_broker_list = list(set(agent_broker_list))
                count = 0
                for agent_id in agent_broker_list:
                    count += Chat.objects.filter(master__domain=site_id, master__seller=agent_id, receiver=agent_id, status=1, is_read=0).count()
                message_count['admin_msg_cnt'] = count
            elif user_type == "agent":
                message_count['admin_msg_cnt'] = Chat.objects.filter(master__domain=site_id, master__seller=user_id, receiver=user_id, status=1, is_read=0).count()
            else:
                message_count['admin_msg_cnt'] = 0
            return Response(response.parsejson("Fetch data.", message_count, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ActiveEventListingApiView(APIView):
    """
    Active event listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            lookup_event = LookupEvent.objects.filter(is_active=1).order_by("-id").values("id", "event_name")
            return Response(response.parsejson("Fetch Data.", lookup_event, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))




