# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.globalfunction import *
from api.users.models import *
from api.blog.serializers import *
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


class BlogSidebarApiView(APIView):
    """
    Blog sidebar
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            network_domain = NetworkDomain.objects.get(id=site_id, is_active=1)
            serializer = BlogSidebarSerializer(network_domain)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontArticleListingApiView(APIView):
    """
    Front article listing
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
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            # min_dt = timezone.now() - timedelta(hours=720)
            max_dt = timezone.now()
            network_articles = NetworkArticles.objects.filter((Q(domain=site_id) | Q(domain__isnull=True)) & Q(status=1) & Q(publish_date__lte=max_dt))
            # -------------Filter--------------
            if "category_id" in data and data['category_id'] != "":
                network_articles = network_articles.filter(asset=int(data['category_id']))
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_articles = network_articles.filter(Q(id=search))
                else:
                    network_articles = network_articles.filter(Q(title__icontains=search) | Q(author_name__icontains=search) | Q(description__icontains=search) | Q(asset__name__icontains=search))
            # --------------------Sorting----------------
            if "sort_by" in data and data['sort_by'] != "" and "sort_order" in data and data['sort_order'] != "":
                if data['sort_order'].lower() == "asc":
                    sort_by = "publish_date"
                else:
                    sort_by = "-publish_date"
                network_articles = network_articles.order_by(sort_by)

            total = network_articles.count()
            network_articles = network_articles.order_by("-id").only("id")[offset:limit]
            serializer = FrontArticleListingSerializer(network_articles, many=True)
            all_data = {"total": total, "data": serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontArticleDetailApiView(APIView):
    """
    Front article detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
            else:
                return Response(response.parsejson("article_id is required", "", status=403))

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            # min_dt = timezone.now() - timedelta(hours=720)
            max_dt = timezone.now()
            network_articles = NetworkArticles.objects.get(id=article_id, domain=site_id, publish_date__lte=max_dt, status=1)
            serializer = FrontArticleDetailSerializer(network_articles)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontArticleSuggestionApiView(APIView):
    """
    Front article suggestion
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

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
            # min_dt = timezone.now() - timedelta(hours=720)
            max_dt = timezone.now()
            network_article = NetworkArticles.objects.annotate(data=F('title')).filter(domain=site_id, data__icontains=search, publish_date__lte=max_dt, status=1).values("data")
            searched_data = searched_data + list(network_article)

            network_article = NetworkArticles.objects.annotate(data=F('asset__name')).filter(domain=site_id, data__icontains=search, publish_date__lte=max_dt, status=1).values("data")
            searched_data = searched_data + list(network_article)

            # network_article = NetworkArticles.objects.annotate(data=F('author_name')).filter(domain=site_id, data__icontains=search).values("data")
            # searched_data = searched_data + list(network_article)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BlogCategoryApiView(APIView):
    """
    Blog category
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            blog_category = NetworkArticleCategory.objects.filter(status=1).values("id", "name")
            return Response(response.parsejson("Fetch data.", blog_category, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddBlogCategoryApiView(APIView):
    """
    Add blog category
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            category_id = None
            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])
                category_id = NetworkArticleCategory.objects.get(id=category_id)
                if not category_id:
                    return Response(response.parsejson("Category does not exist.", "", status=403))

            if "name" in data and data['name'] != "":
                name = data['name']
                article_category = NetworkArticleCategory.objects.filter(name=name)
                if category_id: # exclude current name if update is calling on
                    article_category = article_category.exclude(id=category_id.id)
                article_category = article_category.first()
                if article_category is not None:
                    return Response(response.parsejson("name is already exist.", "", status=403))
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            serializer = BlogCategorySerializer(category_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Added successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BlogCategoryListApiView(APIView):
    """
    Blog category list
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
            article_category = NetworkArticleCategory.objects.order_by("-id")[offset: limit]
            serializer = BlogCategorySerializer(article_category, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BlogCategoryDetailApiView(APIView):
    """
    Blog category detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            category_id = None
            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])
            else:
                return Response(response.parsejson("category_id is required.", "", status=403))
            article_category = NetworkArticleCategory.objects.get(id=category_id)
            serializer = BlogCategorySerializer(article_category)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


