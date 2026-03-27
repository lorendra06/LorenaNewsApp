"""
Views for the LorenasGossip application.
Handles authentication, articles, newsletters,
publisher profiles, and team management.

All views use Django's login_required decorator.
Role-based access is enforced via custom decorators
defined in decorators.py.
"""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import (
    editor_or_journalist_required,
    editor_required,
    journalist_required,
)
from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherTeamForm,
    RegisterForm,
)
from .models import Article, CustomUser, Newsletter

logger = logging.getLogger(__name__)


# ── Authentication


def register_view(request):
    """Register a new user and assign them to the correct group."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(
                    request, f"Welcome, {user.username}!"
                )
                return redirect("article_list")
            except DatabaseError as e:
                logger.error(
                    "Database error during registration: %s", e
                )
                messages.error(
                    request,
                    "Registration failed due to a server error. "
                    "Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    """Login an existing user."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                login(request, user)
                messages.success(
                    request, f"Welcome back, {user.username}!"
                )
                return redirect("article_list")
            except DatabaseError as e:
                logger.error("Unexpected error during login: %s", e)
                messages.error(
                    request, "Login failed. Please try again."
                )
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    """Logout the current user."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


# ── Publishers


@login_required
def publisher_list(request):
    """Display all publishers."""
    try:
        publishers = CustomUser.objects.filter(
            role="publisher"
        ).order_by("username")
    except DatabaseError as e:
        logger.error("Error fetching publishers: %s", e)
        publishers = []
        messages.error(request, "Could not load publishers.")
    return render(
        request,
        "publishers/publisher_list.html",
        {"publishers": publishers},
    )


@login_required
def publisher_detail(request, pk):
    """Display a publisher's profile, team, and articles."""
    publisher = get_object_or_404(CustomUser, pk=pk, role="publisher")
    articles = Article.objects.filter(
        publisher=publisher, approved=True
    )
    return render(
        request,
        "publishers/publisher_detail.html",
        {
            "publisher": publisher,
            "articles": articles,
        },
    )


@login_required
def publisher_team(request, pk):
    """
    Publisher manages their team of journalists and editors.
    Only the publisher themselves can access this page.
    """
    publisher = get_object_or_404(CustomUser, pk=pk, role="publisher")

    if request.user != publisher:
        messages.error(
            request, "You can only manage your own team."
        )
        return redirect("publisher_detail", pk=pk)

    if request.method == "POST":
        form = PublisherTeamForm(request.POST, instance=publisher)
        if form.is_valid():
            try:
                publisher.journalists.set(
                    form.cleaned_data["journalists"]
                )
                publisher.editors.set(
                    form.cleaned_data["editors"]
                )
                messages.success(request, "Team updated successfully!")
                return redirect("publisher_detail", pk=pk)
            except DatabaseError as e:
                logger.error("Error updating team: %s", e)
                messages.error(
                    request,
                    "Could not update team. Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PublisherTeamForm(instance=publisher)

    return render(
        request,
        "publishers/publisher_team.html",
        {"form": form, "publisher": publisher},
    )


@login_required
def join_publisher(request, pk):
    """
    Journalist or editor requests to join a publisher's team.
    Publisher can remove them from the team via publisher_team view.
    """
    publisher = get_object_or_404(CustomUser, pk=pk, role="publisher")

    if request.user.role not in ("journalist", "editor"):
        messages.error(
            request,
            "Only journalists and editors can join a publisher.",
        )
        return redirect("publisher_detail", pk=pk)

    if request.method == "POST":
        try:
            if request.user.role == "journalist":
                publisher.journalists.add(request.user)
            else:
                publisher.editors.add(request.user)
            messages.success(
                request,
                f"You have joined {publisher.username}'s team!",
            )
        except DatabaseError as e:
            logger.error("Error joining publisher team: %s", e)
            messages.error(
                request, "Could not join team. Please try again."
            )
        return redirect("publisher_detail", pk=pk)

    return render(
        request,
        "publishers/publisher_join_confirm.html",
        {"publisher": publisher},
    )


@login_required
def leave_publisher(request, pk):
    """Journalist or editor leaves a publisher's team."""
    publisher = get_object_or_404(CustomUser, pk=pk, role="publisher")

    if request.user.role not in ("journalist", "editor"):
        messages.error(
            request, "Only journalists and editors can leave a team."
        )
        return redirect("publisher_detail", pk=pk)

    if request.method == "POST":
        try:
            if request.user.role == "journalist":
                publisher.journalists.remove(request.user)
            else:
                publisher.editors.remove(request.user)
            messages.success(
                request,
                f"You have left {publisher.username}'s team.",
            )
        except DatabaseError as e:
            logger.error("Error leaving publisher team: %s", e)
            messages.error(
                request, "Could not leave team. Please try again."
            )
        return redirect("publisher_detail", pk=pk)

    return render(
        request,
        "publishers/publisher_leave_confirm.html",
        {"publisher": publisher},
    )


# ── Articles


@login_required
def article_list(request):
    """Display all approved articles."""
    try:
        articles = Article.objects.filter(approved=True)
    except DatabaseError as e:
        logger.error("Error fetching articles: %s", e)
        articles = []
        messages.error(request, "Could not load articles.")
    return render(
        request,
        "articles/article_list.html",
        {"articles": articles},
    )


@login_required
def article_detail(request, pk):
    """Display a single article."""
    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(
        request,
        "articles/article_detail.html",
        {"article": article},
    )


@login_required
@journalist_required
def article_create(request):
    """Create a new article (journalists only)."""
    if request.method == "POST":
        form = ArticleForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                messages.success(request, "Article submitted for review!")
                return redirect("article_list")
            except DatabaseError as e:
                logger.error("Error saving article: %s", e)
                messages.error(
                    request,
                    "Could not save article. Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ArticleForm(user=request.user)
    return render(
        request,
        "articles/article_form.html",
        {"form": form, "action": "Create"},
    )


@login_required
@editor_or_journalist_required
def article_edit(request, pk):
    """Edit an existing article (editors and journalists)."""
    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        form = ArticleForm(
            request.POST, instance=article, user=request.user
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Article updated successfully!")
                return redirect("article_list")
            except DatabaseError as e:
                logger.error("Error updating article %s: %s", pk, e)
                messages.error(
                    request,
                    "Could not update article. Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ArticleForm(instance=article, user=request.user)
    return render(
        request,
        "articles/article_form.html",
        {"form": form, "action": "Edit"},
    )


@login_required
@editor_or_journalist_required
def article_delete(request, pk):
    """Delete an article (editors and journalists)."""
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        try:
            article.delete()
            messages.success(request, "Article deleted.")
        except DatabaseError as e:
            logger.error("Error deleting article %s: %s", pk, e)
            messages.error(
                request,
                "Could not delete article. Please try again.",
            )
        return redirect("article_list")
    return render(
        request,
        "articles/article_confirm_delete.html",
        {"article": article},
    )


# ── Editor: Article Approval


@login_required
@editor_required
def pending_articles(request):
    """List all articles pending approval (editors only)."""
    try:
        articles = Article.objects.filter(approved=False)
    except DatabaseError as e:
        logger.error("Error fetching pending articles: %s", e)
        articles = []
        messages.error(request, "Could not load pending articles.")
    return render(
        request,
        "articles/pending_articles.html",
        {"articles": articles},
    )


@login_required
@editor_required
def approve_article(request, pk):
    """Approve an article (editors only)."""
    article = get_object_or_404(Article, pk=pk)

    if article.approved:
        messages.warning(
            request,
            f'Article "{article.title}" is already approved.',
        )
        return redirect("pending_articles")

    if request.method == "POST":
        try:
            article.approved = True
            article.save(update_fields=["approved"])
            messages.success(
                request,
                f'Article "{article.title}" approved and published!',
            )
        except DatabaseError as e:
            logger.error("Error approving article %s: %s", pk, e)
            messages.error(
                request,
                "Could not approve article. Please try again.",
            )
        return redirect("pending_articles")
    return render(
        request,
        "articles/approve_article.html",
        {"article": article},
    )


# ── Newsletters


@login_required
def newsletter_list(request):
    """Display all newsletters."""
    try:
        newsletters = Newsletter.objects.all()
    except DatabaseError as e:
        logger.error("Error fetching newsletters: %s", e)
        newsletters = []
        messages.error(request, "Could not load newsletters.")
    return render(
        request,
        "newsletters/newsletter_list.html",
        {"newsletters": newsletters},
    )


@login_required
def newsletter_detail(request, pk):
    """Display a single newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(
        request,
        "newsletters/newsletter_detail.html",
        {"newsletter": newsletter},
    )


@login_required
@journalist_required
def newsletter_create(request):
    """Create a new newsletter (journalists only)."""
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            try:
                newsletter = form.save(commit=False)
                newsletter.author = request.user
                newsletter.save()
                form.save_m2m()
                messages.success(request, "Newsletter created!")
                return redirect("newsletter_list")
            except DatabaseError as e:
                logger.error("Error saving newsletter: %s", e)
                messages.error(
                    request,
                    "Could not save newsletter. Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NewsletterForm()
    return render(
        request,
        "newsletters/newsletter_form.html",
        {"form": form, "action": "Create"},
    )


@login_required
@editor_or_journalist_required
def newsletter_edit(request, pk):
    """Edit a newsletter (editors and journalists)."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Newsletter updated!")
                return redirect("newsletter_list")
            except DatabaseError as e:
                logger.error(
                    "Error updating newsletter %s: %s", pk, e
                )
                messages.error(
                    request,
                    "Could not update newsletter. Please try again.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NewsletterForm(instance=newsletter)
    return render(
        request,
        "newsletters/newsletter_form.html",
        {"form": form, "action": "Edit"},
    )


@login_required
@editor_or_journalist_required
def newsletter_delete(request, pk):
    """Delete a newsletter (editors and journalists)."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.method == "POST":
        try:
            newsletter.delete()
            messages.success(request, "Newsletter deleted.")
        except DatabaseError as e:
            logger.error(
                "Error deleting newsletter %s: %s", pk, e
            )
            messages.error(
                request,
                "Could not delete newsletter. Please try again.",
            )
        return redirect("newsletter_list")
    return render(
        request,
        "newsletters/newsletter_confirm_delete.html",
        {"newsletter": newsletter},
    )


# ── Username Recovery


def username_recovery(request):
    """
    Allow users to recover their username via email.
    Displays the username associated with the provided email.
    """
    found_username = None
    not_found = False

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Please enter an email address.")
            return render(
                request,
                "auth/username_recovery.html",
                {"found_username": None, "not_found": False},
            )

        if "@" not in email or "." not in email:
            messages.error(
                request, "Please enter a valid email address."
            )
            return render(
                request,
                "auth/username_recovery.html",
                {"found_username": None, "not_found": False},
            )

        try:
            user = CustomUser.objects.get(email=email)
            found_username = user.username
        except CustomUser.DoesNotExist:
            not_found = True
        except DatabaseError as e:
            logger.error("DB error in username recovery: %s", e)
            messages.error(
                request,
                "A server error occurred. Please try again.",
            )

    return render(
        request,
        "auth/username_recovery.html",
        {
            "found_username": found_username,
            "not_found": not_found,
        },
    )
