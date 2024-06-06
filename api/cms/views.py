# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.cms.models import *
import datetime
from django.utils import timezone
from api.cms.serializers import *
from api.packages.globalfunction import *
from django.db import transaction
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.db.models import F
from django.db.models import Q
from django.conf import settings
from django.db.models import Case, Value, When
from api.packages.mail_service import send_email, compose_email, send_custom_email
from api.packages.common import *

class AddCmsApiView(APIView):
    """
    Add/Update cms
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            cms_id = None
            cms_content = None
            if "cms_id" in data and data['cms_id'] != "":
                cms_id = int(data['cms_id'])
                cms_content = CmsContent.objects.filter(id=cms_id).first()
                if cms_content is None:
                    return Response(response.parsejson("Cms page not exist.", "", status=403))

            site_id = None
            if "site" in data and data['site'] != "":
                site_id = data['site']

            if "page_title" in data and data['page_title'] != "":
                page_title = data['page_title']
            else:
                return Response(response.parsejson("page_title is required.", "", status=403))

            if "meta_key_word" in data and data['meta_key_word'] != "":
                meta_key_word = data['meta_key_word']
            else:
                return Response(response.parsejson("meta_key_word is required.", "", status=403))

            if "meta_description" in data and data['meta_description'] != "":
                meta_description = data['meta_description']
            else:
                return Response(response.parsejson("meta_description is required.", "", status=403))

            if "meta_title" in data and data['meta_title'] != "":
                meta_title = data['meta_title']
            else:
                return Response(response.parsejson("meta_title is required.", "", status=403))

            if "slug" in data and data['slug'] != "":
                slug = data['slug']
                cms = CmsContent.objects.filter(slug=slug, site=site_id).exclude(id=cms_id).first()
                if cms is not None:
                    return Response(response.parsejson("slug already exist.", "", status=403))
            else:
                return Response(response.parsejson("slug is required.", "", status=403))

            if "page_content" in data and data['page_content'] != "":
                page_content = data['page_content']
            else:
                return Response(response.parsejson("page_content is required.", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = data['added_by']
                data['updated_by'] = data['added_by']
            else:
                return Response(response.parsejson("added_by is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required.", "", status=403))
            serializer = CmsContentSerializer(cms_content, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Cms added/updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CmsDetailApiView(APIView):
    """
    Cms detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "cms_id" in data and data['cms_id'] != "":
                cms_id = int(data['cms_id'])
                cms_content = CmsContent.objects.filter(id=cms_id).first()
                if cms_content is None:
                    return Response(response.parsejson("Cms page not exist.", "", status=403))
            else:
                return Response(response.parsejson("cms_id is required.", "", status=403))
            cms_content = CmsContent.objects.filter(id=cms_id).first()
            serializer = CmsDetailSerializer(cms_content)
            return Response(response.parsejson("Fetch Data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CmsChangeStatusApiView(APIView):
    """
    Cms change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "cms_id" in data and data['cms_id'] != "":
                cms_id = int(data['cms_id'])
                cms_content = CmsContent.objects.filter(id=cms_id).first()
                if cms_content is None:
                    return Response(response.parsejson("Cms page not exist.", "", status=403))
            else:
                return Response(response.parsejson("cms_id is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            CmsContent.objects.filter(id=cms_id).update(status=status)
            return Response(response.parsejson("Cms status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminCmsListingApiView(APIView):
    """
    Site Setting listing
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

            cms_content = CmsContent.objects.filter(id__gte=1)
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                cms_content = cms_content.filter(status__in=data["status"])
            if "site_id" in data and type(data["site_id"]) == list and len(data["site_id"]) > 0:
                cms_content = cms_content.filter(site__in=data["site_id"])
            else:
                cms_content = cms_content.filter(site__isnull=True)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    cms_content = cms_content.filter(Q(id=search) | Q(site=search))
                else:
                    cms_content = cms_content.filter(Q(page_title__icontains=search) | Q(meta_key_word__icontains=search) | Q(meta_title__icontains=search) | Q(site__domain_name__icontains=search))
            total = cms_content.count()
            cms_content = cms_content.only('id')[offset: limit]
            serializer = AdminCmsListingSerializer(cms_content, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminArticleListingApiView(APIView):
    """
    Admin Article listing
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

            network_articles = NetworkArticles.objects
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                network_articles = network_articles.filter(status__in=data["status"])
            if "site_id" in data and type(data["site_id"]) == list and len(data["site_id"]) > 0:
                network_articles = network_articles.filter(domain__in=data["site_id"])
            else:
                network_articles = network_articles.filter(domain__isnull=True)
            if "asset_type" in data and type(data["asset_type"]) == list and len(data["asset_type"]) > 0:
                network_articles = network_articles.filter(asset__in=data["asset_type"])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_articles = network_articles.filter(Q(id=search))
                else:
                    network_articles = network_articles\
                        .filter(
                            Q(title__icontains=search) |
                            Q(author_name__icontains=search) |
                            Q(asset__name__icontains=search) |
                            Q(domain__domain_name__icontains=search)
                        )

            total = network_articles.count()
            network_articles = network_articles.order_by("-id").only("id")[offset:limit]
            serializer = AdminArticleListingSerializer(network_articles, many=True)
            all_data = {"total": total, "data": serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminAddArticleApiView(APIView):
    """
    Admin Add/Update article
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            site_id = None
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id

            article_id = None
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
                article_id = NetworkArticles.objects.get(id=article_id)

            required_field = ['title', "description", "author_name", "status", "user_id", "asset"]
            for field in required_field:
                if field in data and data[field] != "":
                    field = data[field]
                else:
                    return Response(response.parsejson(field+" is required", "", status=403))

            if "author_image" in data and data['author_image'] != "":
                author_image = int(data['author_image'])
            else:
                data['author_image'] = None

            if "upload" in data and data['upload'] != "":
                upload = int(data['upload'])
            else:
                data['upload'] = None
            if article_id is None:
                data['added_by'] = data['user_id']
            else:
                data['added_by'] = article_id.added_by_id
            data['updated_by'] = data['user_id']
            serializer = AdminAddArticleSerializer(article_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Article successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminArticleDetailApiView(APIView):
    """
    Admin Article detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
            else:
                return Response(response.parsejson("article_id is required", "", status=403))

            network_articles = NetworkArticles.objects.get(id=article_id)
            serializer = AdminArticleDetailSerializer(network_articles)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminArticleChangeStatusApiView(APIView):
    """
    Admin article change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
            else:
                return Response(response.parsejson("article_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))
            NetworkArticles.objects.filter(id=article_id).update(status=status)
            return Response(response.parsejson("Status successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetPageApiView(APIView):
    """
    Get page
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "slug" in data and data['slug'] != "":
                slug = data['slug']
            else:
                return Response(response.parsejson("slug is required", "", status=403))

            if "site_id" in data and data['site_id'] != "":
                site_id = data['site_id']
            else:
                return Response(response.parsejson("site_id is required.", "", status=403))

            cms = CmsContent.objects.filter(site=site_id, slug=slug, status=1).first()
            if cms is None:
                cms = CmsContent.objects.filter(site__isnull=True, slug=slug, status=1).first()
            serializer = CmsContentSerializer(cms)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetAuctionTypeApiView(APIView):
    """
    Get auction type
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            slug = "auction-type"
            if "site_id" in data and data['site_id'] != "":
                site_id = data['site_id']
            else:
                return Response(response.parsejson("site_id is required.", "", status=403))

            cms = CmsContent.objects.filter((Q(site=site_id) | Q(site__isnull=True)) & Q(slug=slug) & Q(status=1)).order_by(F("site").asc(nulls_last=True)).first()

            serializer = CmsContentSerializer(cms)
            # auction_type = LookupAuctionType.objects.filter(is_active=1).values("id", "auction_type")
            auction_type = NetworkAuction.objects.filter(domain=site_id, status=1).values("id", auction_type=F("auction_name"))
            all_data = {
                "data": serializer.data,
                "auction_type": auction_type
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AboutDetailApiView(APIView):
    """
    About detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = data['site_id']
            else:
                return Response(response.parsejson("site_id is required.", "", status=403))
            try:
                cms = CmsContent.objects.filter(site=site_id, slug="about-us", status=1).first()
                if cms is None:
                    cms = CmsContent.objects.filter(site__isnull=True, slug="about-us", status=1).first()
                serializer = CmsContentSerializer(cms)
                content = serializer.data
            except Exception as exp:
                content = {}

            try:
                blog = NetworkArticles.objects.filter(domain=site_id, status=1).order_by("-id")[0: 4]
                blog_serializer = ArticleDetailSerializer(blog, many=True)
                blog = blog_serializer.data
            except Exception as exp:
                blog = []

            try:
                profile = UserBusinessProfile.objects.get(user__site=site_id)
                profile_serializer = AboutProfileSerializer(profile)
                profile = profile_serializer.data
            except Exception as exp:
                profile = {}

            all_data = {
                "content": content,
                "blog": blog,
                "profile": profile
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ContactDetailApiView(APIView):
    """
    Contact detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = data['site_id']
            else:
                return Response(response.parsejson("site_id is required.", "", status=403))
            try:
                cms = CmsContent.objects.filter(site=site_id, slug="contact-us", status=1).first()
                if cms is None:
                    cms = CmsContent.objects.filter(site__isnull=True, slug="contact-us", status=1).first()
                serializer = CmsContentSerializer(cms)
                content = serializer.data
            except Exception as exp:
                content = {}

            try:
                profile = UserBusinessProfile.objects.get(user__site=site_id)
                profile_serializer = AboutProfileSerializer(profile)
                profile = profile_serializer.data
            except Exception as exp:
                profile = {}

            try:
                social_account = NetworkSocialAccount.objects.filter(domain=site_id, status=1, url__isnull=False).order_by("position")
                social_account_serializer = SocialAccountSerializer(social_account, many=True)
                social_account = social_account_serializer.data
            except Exception as exp:
                social_account = []

            all_data = {
                "content": content,
                "profile": profile,
                "social_account": social_account
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SaveContactApiView(APIView):
    """
    Save contact
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                data['domain'] = site_id
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
            else:
                return Response(response.parsejson("site_id is required.", "", status=403))
            data['status'] = 1
            serializer = SaveContactSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                email = data['email']
                first_name = data['first_name']
                message = data['message']
                phone_no = data['phone_no']
                user_type = data['user_type'] 
                #Email send
                broker_data = Users.objects.filter(site_id=site_id).first()
                site_owner = Users.objects.filter(site=site_id).first()
                site_owner = site_owner.id
                user_subscription = UserSubscription.objects.filter(user=site_owner, subscription_status=1).first()
                exit_plan = int(user_subscription.payment_amount)
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                domain_url = subdomain_url.replace("###", domain_name)
                template_data = {"domain_id": site_id, "slug": "contact_us"}
                extra_data = {"user_name": first_name, "chat_messge": message, "web_url": settings.FRONT_BASE_URL, "dashboard_link": domain_url, "domain_id": site_id}
                compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
                template_data = {"domain_id": site_id, "slug": "contact_us_broker"}
                if exit_plan > 0:
                    if user_type.lower() == 'seller':
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/contact-listing/?user_type=seller"
                    elif user_type.lower() == 'buyer':
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/contact-listing/?user_type=buyer"
                    elif user_type.lower() == 'agent':
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/contact-listing/?user_type=agent"
                    else:
                        domain_url = subdomain_url.replace("###", domain_name)+"admin/contact-listing/?user_type="
                    domain_img = 'dashboard-btn.jpg'
                else:
                    domain_img = 'website-btn.jpg'
                    domain_url = subdomain_url.replace("###", domain_name)
                extra_data = {"user_name": broker_data.first_name, "chat_messge": message, "web_url": settings.FRONT_BASE_URL, "dashboard_link": domain_url, "domain_id": site_id, 'name': first_name, 'email': email, 'phone': phone_format(phone_no), 'user_type': user_type, 'message': message, 'domain_link_img': domain_img}
                compose_email(to_email=[broker_data.email], template_data=template_data, extra_data=extra_data)
                
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Your query send successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainContactSuggestionApiView(APIView):
    """
    Subdomain contact suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            contact = ContactUs.objects.annotate(data=F('first_name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(contact)

            contact = ContactUs.objects.annotate(data=F('email')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(contact)

            contact = ContactUs.objects.annotate(data=F('phone_no')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(contact)

            contact = ContactUs.objects.annotate(data=F('user_type')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(contact)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class VideoTutorialsApiView(APIView):
    """
    Video tutorials
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

            video_tutorials = VideoTutorials.objects.filter(Q(domain=site_id))
            if video_tutorials is None:
                video_tutorials = VideoTutorials.objects.filter(Q(domain__isnull=True))
            video_tutorials = video_tutorials.filter(status=1)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    video_tutorials = video_tutorials.filter(Q(id=search) | Q(domain=search))
                else:
                    video_tutorials = video_tutorials.filter(Q(title__icontains=search) | Q(description__icontains=search))
            total = video_tutorials.count()
            video_tutorials = video_tutorials.order_by("-id").only('id')[offset: limit]
            serializer = VideoTutorialsSerializer(video_tutorials, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminVideoTutorialsListingApiView(APIView):
    """
    Super admin video tutorials listing
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

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("Not super admin.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            site_id = None
            if "site_id" in data and type(data['site_id']) == list and len(data['site_id']) > 0:
                site_id = data['site_id']

            video_tutorials = VideoTutorials.objects.exclude(status=5)
            if site_id is not None:
                video_tutorials = video_tutorials.filter(domain__in=site_id)
            else:
                video_tutorials = video_tutorials.filter(domain__isnull=True)

            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                video_tutorials = video_tutorials.filter(status__in=data['status'])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    video_tutorials = video_tutorials.filter(Q(id=search) | Q(domain__domain_name__icontains=search))
                else:
                    video_tutorials = video_tutorials.filter(Q(title__icontains=search) | Q(domain__domain_name__icontains=search))
            total = video_tutorials.count()
            video_tutorials = video_tutorials.order_by("-id").only('id')[offset: limit]
            serializer = SuperAdminVideoTutorialsListingSerializer(video_tutorials, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminAddVideoTutorialsApiView(APIView):
    """
    Super admin add video tutorials
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("Not super admin.", "", status=201))
                data['added_by'] = user_id
                data['updated_by'] = user_id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            site_id = None
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id

            video_id = None
            if "video_id" in data and data['video_id'] != "":
                video_id = int(data['video_id'])
                video_id = VideoTutorials.objects.get(id=video_id)

            if "title" in data and data['title'] != "":
                title = data['title']
            else:
                return Response(response.parsejson("title is required", "", status=403))

            if "description" in data and data['description'] != "":
                description = data['description']
            else:
                return Response(response.parsejson("description is required", "", status=403))

            if "video_url" in data and data['video_url'] != "":
                video_url = data['video_url']
            else:
                return Response(response.parsejson("video_url is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            serializer = SuperAdminAddVideoTutorialsSerializer(video_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))

            return Response(response.parsejson("Added/Updated Successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminVideoTutorialsDetailApiView(APIView):
    """
    Super admin video tutorials detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("Not super admin.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "video_id" in data and data['video_id'] != "":
                video_id = int(data['video_id'])
            else:
                return Response(response.parsejson("video_id is required", "", status=403))

            video_tutorials = VideoTutorials.objects.get(id=video_id)
            serializer = SuperAdminAddVideoTutorialsSerializer(video_tutorials)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainCmsApiView(APIView):
    """
    Subdomain cms
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
                user = Users.objects.filter(id=user_id, status=1, user_type=2, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, user__user_type=2, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised  user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            slug_list = ["about-us", "contact-us", "terms", "privacy-policy"]
            if "slug" in data and data['slug'] != "" and data['slug'] in slug_list:
                slug = data['slug']
            else:
                return Response(response.parsejson("slug is required", "", status=403))
            cms_content = CmsContent.objects.filter(Q(slug=slug) & (Q(site=domain) | Q(site__isnull=True))).order_by(F("site").asc(nulls_last=True)).first()
            serializer = SubdomainCmsSerializer(cms_content)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainCmsUpdateApiView(APIView):
    """
    Subdomain cms update
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
                data['site'] = domain
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=2, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, user__user_type=2, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised  user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "cms_id" in data and data['cms_id'] != "":
                cms_id = data['cms_id']
            else:
                return Response(response.parsejson("cms_id is required", "", status=403))

            if "page_title" in data and data['page_title'] != "":
                page_title = data['page_title']
            else:
                return Response(response.parsejson("page_title is required.", "", status=403))

            if "meta_key_word" in data and data['meta_key_word'] != "":
                meta_key_word = data['meta_key_word']
            else:
                return Response(response.parsejson("meta_key_word is required.", "", status=403))

            if "meta_description" in data and data['meta_description'] != "":
                meta_description = data['meta_description']
            else:
                return Response(response.parsejson("meta_description is required.", "", status=403))

            if "meta_title" in data and data['meta_title'] != "":
                meta_title = data['meta_title']
            else:
                return Response(response.parsejson("meta_title is required.", "", status=403))

            slug_list = ["about-us", "contact-us", "terms", "privacy-policy"]
            if "slug" in data and data['slug'] != "" and data['slug'] in slug_list:
                slug = data['slug']
                cms = CmsContent.objects.filter(slug=slug, site=domain).exclude(id=cms_id).first()
                if cms is not None:
                    return Response(response.parsejson("slug already exist.", "", status=403))
            else:
                return Response(response.parsejson("slug is required.", "", status=403))

            if "page_content" in data and data['page_content'] != "":
                page_content = data['page_content']
            else:
                return Response(response.parsejson("page_content is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            data['added_by'] = user_id
            data['updated_by'] = user_id

            cms_content = CmsContent.objects.filter(id=cms_id).first()
            if cms_content is None:
                return Response(response.parsejson("Cms not exist.", "", status=403))
            if cms_content.site_id == domain:
                serializer = CmsContentSerializer(cms_content, data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            else:
                serializer = CmsContentSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))



