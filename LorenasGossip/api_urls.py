"""
URL patterns for the LorenasGossip REST API.
All routes are prefixed with /api/ in the main urls.py.
"""

from django.urls import path

from .api_views import (
    ApprovedArticleLogAPIView,
    ApproveArticleAPIView,
    ArticleDetailAPIView,
    ArticleListAPIView,
    ArticleSubscribedAPIView,
    LoginAPIView,
    LogoutAPIView,
    NewsletterListAPIView,
    PublisherDetailAPIView,
    PublisherJoinAPIView,
    PublisherLeaveAPIView,
    PublisherListAPIView,
    PublisherTeamAPIView,
)

urlpatterns = [
    # ── Auth
    path("login/", LoginAPIView.as_view(), name="api_login"),
    path("logout/", LogoutAPIView.as_view(), name="api_logout"),
    # ── Publishers
    path(
        "publishers/",
        PublisherListAPIView.as_view(),
        name="api_publisher_list",
    ),
    path(
        "publishers/<int:pk>/",
        PublisherDetailAPIView.as_view(),
        name="api_publisher_detail",
    ),
    path(
        "publishers/<int:pk>/team/",
        PublisherTeamAPIView.as_view(),
        name="api_publisher_team",
    ),
    path(
        "publishers/<int:pk>/join/",
        PublisherJoinAPIView.as_view(),
        name="api_publisher_join",
    ),
    path(
        "publishers/<int:pk>/leave/",
        PublisherLeaveAPIView.as_view(),
        name="api_publisher_leave",
    ),
    # ── Articles
    path(
        "articles/",
        ArticleListAPIView.as_view(),
        name="api_article_list",
    ),
    path(
        "articles/subscribed/",
        ArticleSubscribedAPIView.as_view(),
        name="api_article_subscribed",
    ),
    path(
        "articles/<int:pk>/",
        ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "articles/<int:pk>/approve/",
        ApproveArticleAPIView.as_view(),
        name="api_article_approve",
    ),
    # ── Approved log (used by signal)
    path(
        "approved/",
        ApprovedArticleLogAPIView.as_view(),
        name="api_approved_log",
    ),
    # ── Newsletters
    path(
        "newsletters/",
        NewsletterListAPIView.as_view(),
        name="api_newsletter_list",
    ),
]
