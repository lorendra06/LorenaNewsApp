"""
Admin configuration for LorenasGossip models.
Registers CustomUser, Article, and Newsletter with the admin site.
Publisher is now a role on CustomUser, not a separate model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, CustomUser, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin view for CustomUser model."""

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Role & Subscriptions",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                    "journalists",
                    "editors",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin view for Article model."""

    list_display = ("title", "author", "publisher", "approved", "created_at")
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "author__username")
    ordering = ("-created_at",)
    list_editable = ("approved",)
    actions = ["approve_articles"]

    @admin.action(description="Approve selected articles")
    def approve_articles(self, request, queryset):
        """Bulk approve selected articles."""
        queryset.update(approved=True)
        self.message_user(
            request, f"{queryset.count()} article(s) approved successfully."
        )


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin view for Newsletter model."""

    list_display = ("title", "author", "created_at")
    search_fields = ("title", "author__username")
    ordering = ("-created_at",)
    filter_horizontal = ("articles",)
