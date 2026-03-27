"""
Main URL configuration for the LorenaNewsApp project.
Includes routes for admin, web app, REST API, and password management.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    # ── Django admin
    path("admin/", admin.site.urls),
    # ── Main app
    path("", include("LorenasGossip.urls")),
    # ── REST API
    path("api/", include("LorenasGossip.api_urls")),
    # ── Password reset (for logged out users)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset.html",
            email_template_name="auth/password_reset_email.html",
            subject_template_name="auth/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    # ── Password change (for logged in users)
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="auth/password_change.html",
            success_url="/password-change/done/",
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="auth/password_change_done.html",
        ),
        name="password_change_done",
    ),
]
