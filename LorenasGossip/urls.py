"""
URL patterns for the LorenasGossip web application.
All routes are included in the main urls.py.
"""

from django.urls import path

from . import views

urlpatterns = [
    # ── Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "username-recovery/",
        views.username_recovery,
        name="username_recovery",
    ),

    # ── Publishers
    path(
        "publishers/",
        views.publisher_list,
        name="publisher_list",
    ),
    path(
        "publishers/<int:pk>/",
        views.publisher_detail,
        name="publisher_detail",
    ),
    path(
        "publishers/<int:pk>/team/",
        views.publisher_team,
        name="publisher_team",
    ),
    path(
        "publishers/<int:pk>/join/",
        views.join_publisher,
        name="join_publisher",
    ),
    path(
        "publishers/<int:pk>/leave/",
        views.leave_publisher,
        name="leave_publisher",
    ),

    # ── Articles
    path("", views.article_list, name="article_list"),
    path(
        "articles/<int:pk>/",
        views.article_detail,
        name="article_detail",
    ),
    path(
        "articles/create/",
        views.article_create,
        name="article_create",
    ),
    path(
        "articles/<int:pk>/edit/",
        views.article_edit,
        name="article_edit",
    ),
    path(
        "articles/<int:pk>/delete/",
        views.article_delete,
        name="article_delete",
    ),

    # ── Editor approval
    path(
        "articles/pending/",
        views.pending_articles,
        name="pending_articles",
    ),
    path(
        "articles/<int:pk>/approve/",
        views.approve_article,
        name="approve_article",
    ),

    # ── Newsletters
    path(
        "newsletters/",
        views.newsletter_list,
        name="newsletter_list",
    ),
    path(
        "newsletters/<int:pk>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    path(
        "newsletters/create/",
        views.newsletter_create,
        name="newsletter_create",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_edit,
        name="newsletter_edit",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),
]
