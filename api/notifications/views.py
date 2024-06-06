# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.notifications.models import *
from api.notifications.serializers import *
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from api.packages.mail_service import send_email, compose_email, send_custom_email


class TemplateListingApiView(APIView):
    """
    Template listing
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

            notification_template = NotificationTemplate.objects
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                notification_template = notification_template.filter(status__in=data["status"])
            if "site_id" in data and type(data["site_id"]) == list and len(data["site_id"]) > 0:
                notification_template = notification_template.filter(site__in=data["site_id"])
            else:
                notification_template = notification_template.filter(site__isnull=True)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    notification_template = notification_template.filter(Q(id=search))
                else:
                    notification_template = notification_template.filter(Q(event__event_name__icontains=search) | Q(email_subject__icontains=search) | Q(site__domain_name__icontains=search) | Q(site__domain_name__icontains=search) | Q(event__slug__icontains=search))

            total = notification_template.count()
            notification_template = notification_template.order_by("-id").only('id')[offset:limit]
            serializer = TemplateListingSerializer(notification_template, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddTemplateApiView(APIView):
    """
    Add template
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                data["added_by"] = user_id
                data["updated_by"] = user_id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            template_id = None
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
                template_id = NotificationTemplate.objects.filter(id=template_id).first()
                if template_id is None:
                    return Response(response.parsejson("Template not exist.", "", status=403))
                data["added_by"] = template_id.added_by_id

            if "site" in data and data['site'] != "":
                site = int(data['site'])
                network = NetworkDomain.objects.filter(id=site).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))

            if "event" in data and data['event'] != "":
                event = int(data['event'])
                event = LookupEvent.objects.filter(id=event, is_active=1).first()
                if event is None:
                    return Response(response.parsejson("Event not exist.", "", status=403))
            else:
                return Response(response.parsejson("event is required", "", status=403))

            if "email_subject" in data and data['email_subject'] != "":
                email_subject = data['email_subject']
            else:
                return Response(response.parsejson("email_subject is required", "", status=403))

            if "email_content" in data and data['email_content'] != "":
                email_content = data['email_content']
            else:
                return Response(response.parsejson("email_content is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            serializer = AddTemplateSerializer(template_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Template updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TemplateDetailApiView(APIView):
    """
    Template detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
            else:
                return Response(response.parsejson("template_id is required", "", status=403))

            template = NotificationTemplate.objects.get(id=template_id)
            serializer = TemplateDetailSerializer(template)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TemplateChangeStatusApiView(APIView):
    """
    Template change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
            else:
                return Response(response.parsejson("template_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            NotificationTemplate.objects.filter(id=template_id).update(status=status)
            return Response(response.parsejson("Status change successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainTemplateListingApiView(APIView):
    """
    Subdomain template listing
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

            notification_template = NotificationTemplate.objects.filter(site=domain_id)
            if "status" in data and data['status'] != "":
                notification_template = notification_template.filter(status=data["status"])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    notification_template = notification_template.filter(Q(id=search))
                else:
                    notification_template = notification_template.filter(Q(event__event_name__icontains=search) | Q(email_subject__icontains=search) | Q(event__slug__icontains=search))

            total = notification_template.count()
            notification_template = notification_template.order_by("-id").only('id')[offset:limit]
            serializer = SubdomainTemplateListingSerializer(notification_template, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainAddTemplateApiView(APIView):
    """
    Add template
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site" in data and data['site'] != "":
                site = int(data['site'])
                network = NetworkDomain.objects.filter(id=site).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                data["added_by"] = user_id
                data["updated_by"] = user_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            template_id = None
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
                template_id = NotificationTemplate.objects.filter(id=template_id).first()
                if template_id is None:
                    return Response(response.parsejson("Template not exist.", "", status=403))
                data["added_by"] = template_id.added_by_id

            if "event" in data and data['event'] != "":
                event = int(data['event'])
                event = LookupEvent.objects.filter(id=event, is_active=1).first()
                if event is None:
                    return Response(response.parsejson("Event not exist.", "", status=403))
            else:
                return Response(response.parsejson("event is required", "", status=403))

            if "email_subject" in data and data['email_subject'] != "":
                email_subject = data['email_subject']
            else:
                return Response(response.parsejson("email_subject is required", "", status=403))

            if "email_content" in data and data['email_content'] != "":
                email_content = data['email_content']
            else:
                return Response(response.parsejson("email_content is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))
            if template_id is None:
                notification_template = NotificationTemplate.objects.filter(site=site, event=event).first()
                if notification_template is not None:
                    return Response(response.parsejson("Template already exist.", "", status=403))

            serializer = AddTemplateSerializer(template_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Template added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainTemplateDetailApiView(APIView):
    """
    Template detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site" in data and data['site'] != "":
                site = int(data['site'])
                network = NetworkDomain.objects.filter(id=site).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
            else:
                return Response(response.parsejson("template_id is required", "", status=403))

            template = NotificationTemplate.objects.get(id=template_id, site=site)
            serializer = SubdomainTemplateDetailSerializer(template)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainTemplateSuggestionApiView(APIView):
    """
    Subdomain template suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            notification_template = NotificationTemplate.objects.annotate(data=F('email_subject')).filter(site=domain, data__icontains=search).values("data")
            searched_data = searched_data + list(notification_template)

            notification_template = NotificationTemplate.objects.annotate(data=F('event__event_name')).filter(site=domain, data__icontains=search).values("data")
            searched_data = searched_data + list(notification_template)

            notification_template = NotificationTemplate.objects.annotate(data=F('event__slug')).filter(site=domain, data__icontains=search).values("data")
            searched_data = searched_data + list(notification_template)

            # notification_template = NotificationTemplate.objects.annotate(data=F('site__domain_name')).filter(site=domain, data__icontains=search).values("data")
            # searched_data = searched_data + list(notification_template)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NotificationDetailApiView(APIView):
    """
    Notification detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            notification_detail = EventNotification.objects.filter(domain=domain, user=user_id, status=1).order_by("-id").only("id")[0: 4]
            serializer = NotificationDetailSerializer(notification_detail, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NotificationReadApiView(APIView):
    """
    Notification read
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            notification_detail = EventNotification.objects.filter(domain=domain, user=user_id).update(is_read=1)
            return Response(response.parsejson("Successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NotificationCountApiView(APIView):
    """
    Notification count
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            # else:
            #     return Response(response.parsejson("user_id is required", "", status=403))

            notification = EventNotification.objects.filter(domain=domain, user=user_id, is_read=0, status=1).count()
            data = {"count": notification}
            return Response(response.parsejson("Fetch data.", data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NotificationListingApiView(APIView):
    """
    Notification listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

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

            notification_detail = EventNotification.objects.filter(domain=domain, user=user_id, status=1).order_by("-id").only("id")
            total = notification_detail.count()
            notification_detail = notification_detail[offset: limit]
            serializer = NotificationListingSerializer(notification_detail, many=True)
            all_data = {"data": serializer.data, "total": total}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
        

class TemplateListApiView(APIView):
    """
    Template List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            notification_template = NotificationTemplate.objects.filter(site=None, status=1).order_by("event__event_name").only('id')
            serializer = TemplateListSerializer(notification_template, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403)) 


class VerifyEmailApiView(APIView):
    """
    Verify Email
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
            
            if "params_data" in data and data['params_data'] != "" and len(data['params_data']) > 0:
                params_data = data['params_data']
            else:
                return Response(response.parsejson("params_data is required", "", status=403))
            
            if "template_id" in data and data['template_id'] != "":
                template_id = int(data['template_id'])
            else:
                return Response(response.parsejson("template_id is required", "", status=403))
            
            if "email_to" in data and data['email_to'] != "":
                email_to = data['email_to']
            else:
                return Response(response.parsejson("email_to is required", "", status=403))
            notification_template = NotificationTemplate.objects.filter(id=template_id).first()
            slug = notification_template.event.slug
            extra_data = params_data
            template_data = {"slug": slug, "domain_id": domain_id}
            compose_email(to_email=[email_to], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Email Sent Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))                


