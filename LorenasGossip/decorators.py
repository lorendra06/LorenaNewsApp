"""
Custom decorators for role-based access control.
Used in views to restrict access based on the user's role field
instead of relying on Django's permission_required decorator.

Usage:
    @login_required
    @journalist_required
    def my_view(request):
        ...
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def journalist_required(view_func):
    """
    Decorator that restricts access to users with the
    'journalist' role. Returns 403 for other roles.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != "journalist":
            messages.error(
                request,
                "Only journalists can access this page.",
            )
            return redirect("article_list")
        return view_func(request, *args, **kwargs)

    return wrapper


def editor_required(view_func):
    """
    Decorator that restricts access to users with the
    'editor' role. Returns 403 for other roles.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != "editor":
            messages.error(
                request,
                "Only editors can access this page.",
            )
            return redirect("article_list")
        return view_func(request, *args, **kwargs)

    return wrapper


def editor_or_journalist_required(view_func):
    """
    Decorator that restricts access to users with
    'editor' or 'journalist' roles.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ("editor", "journalist"):
            messages.error(
                request,
                "Only editors and journalists can access this page.",
            )
            return redirect("article_list")
        return view_func(request, *args, **kwargs)

    return wrapper


def publisher_required(view_func):
    """
    Decorator that restricts access to users with the
    'publisher' role.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != "publisher":
            messages.error(
                request,
                "Only publishers can access this page.",
            )
            return redirect("article_list")
        return view_func(request, *args, **kwargs)

    return wrapper
