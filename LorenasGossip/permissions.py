"""
Custom DRF permissions based on user role.
"""

from rest_framework.permissions import BasePermission


class IsReader(BasePermission):
    """Allow access only to users with the Reader role."""

    message = "Only readers can access this endpoint."

    def has_permission(self, request, view):
        """Check if user is authenticated and has Reader role."""
        return request.user.is_authenticated and request.user.role == "reader"


class IsJournalist(BasePermission):
    """Allow access only to users with the Journalist role."""

    message = "Only journalists can access this endpoint."

    def has_permission(self, request, view):
        """Check if user is authenticated and has Journalist role."""
        return (
            request.user.is_authenticated and request.user.role == "journalist"
        )


class IsEditor(BasePermission):
    """Allow access only to users with the Editor role."""

    message = "Only editors can access this endpoint."

    def has_permission(self, request, view):
        """Check if user is authenticated and has Editor role."""
        return request.user.is_authenticated and request.user.role == "editor"


class IsPublisher(BasePermission):
    """Allow access only to users with the Publisher role."""

    message = "Only publishers can access this endpoint."

    def has_permission(self, request, view):
        """Check if user is authenticated and has Publisher role."""
        return (
            request.user.is_authenticated and request.user.role == "publisher"
        )


class IsEditorOrJournalist(BasePermission):
    """Allow access to editors and journalists."""

    message = "Only editors or journalists can access this endpoint."

    def has_permission(self, request, view):
        """Check if user has Editor or Journalist role."""
        return request.user.is_authenticated and request.user.role in (
            "editor",
            "journalist",
        )
