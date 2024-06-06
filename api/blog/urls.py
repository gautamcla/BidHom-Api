# -*- coding: utf-8 -*-
from django.urls import path, include
from . import views
from api.blog.views import *

urlpatterns = [
    path("blog-sidebar/", BlogSidebarApiView.as_view()),
    path("front-article-listing/", FrontArticleListingApiView.as_view()),
    path("front-article-detail/", FrontArticleDetailApiView.as_view()),
    path("front-article-suggestion/", FrontArticleSuggestionApiView.as_view()),
    path("blog-category/", BlogCategoryApiView.as_view()),
    path("add-blog-category/", AddBlogCategoryApiView.as_view()),
    path("blog-category-list/", BlogCategoryListApiView.as_view()),
    path("blog-category-detail/", BlogCategoryDetailApiView.as_view()),
]
