"""
RESTful API views for LorenasGossip.
Uses DRF Token Authentication and role-based permissions.
"""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, CustomUser, Newsletter
from .permissions import IsEditor, IsJournalist, IsPublisher
from .serializers import (
    ApprovedArticleLogSerializer,
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    PublisherTeamSerializer,
)


# ── Auth


class LoginAPIView(APIView):
    """
    POST /api/login/
    Returns a token for valid credentials.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user and return token."""
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "username": user.username,
                "role": user.role,
            }
        )


class LogoutAPIView(APIView):
    """
    POST /api/logout/
    Deletes the user's token.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Delete token to logout."""
        request.user.auth_token.delete()
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


# ── Publishers


class PublisherListAPIView(APIView):
    """
    GET /api/publishers/
    Returns a list of all publishers.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all publishers."""
        publishers = CustomUser.objects.filter(role="publisher")
        serializer = PublisherSerializer(publishers, many=True)
        return Response(serializer.data)


class PublisherDetailAPIView(APIView):
    """
    GET /api/publishers/<id>/
    Returns a single publisher with their team.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Return a single publisher."""
        try:
            publisher = CustomUser.objects.get(pk=pk, role="publisher")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PublisherSerializer(publisher)
        return Response(serializer.data)


class PublisherTeamAPIView(APIView):
    """
    GET  /api/publishers/<id>/team/
         Returns the publisher's journalists and editors.
    POST /api/publishers/<id>/team/
         Publisher updates their team (adds/removes members).
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Return the publisher's team."""
        try:
            publisher = CustomUser.objects.get(pk=pk, role="publisher")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PublisherTeamSerializer(publisher)
        return Response(serializer.data)

    def post(self, request, pk):
        """
        Update the publisher's team.
        Only the publisher themselves can update their team.
        """
        if not IsPublisher().has_permission(request, self):
            return Response(
                {"error": "Only publishers can manage their team."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            publisher = CustomUser.objects.get(pk=pk, role="publisher")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user != publisher:
            return Response(
                {"error": "You can only manage your own team."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PublisherTeamSerializer(
            publisher, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class PublisherJoinAPIView(APIView):
    """
    POST /api/publishers/<id>/join/
    Journalist or editor joins a publisher's team.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Join a publisher's team."""
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {
                    "error": (
                        "Only journalists and editors " "can join a publisher."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            publisher = CustomUser.objects.get(pk=pk, role="publisher")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "journalist":
            publisher.journalists.add(request.user)
        else:
            publisher.editors.add(request.user)

        return Response(
            {"message": f"Joined {publisher.username}'s team."},
            status=status.HTTP_200_OK,
        )


class PublisherLeaveAPIView(APIView):
    """
    POST /api/publishers/<id>/leave/
    Journalist or editor leaves a publisher's team.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Leave a publisher's team."""
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {
                    "error": (
                        "Only journalists and editors " "can leave a team."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            publisher = CustomUser.objects.get(pk=pk, role="publisher")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "journalist":
            publisher.journalists.remove(request.user)
        else:
            publisher.editors.remove(request.user)

        return Response(
            {"message": f"Left {publisher.username}'s team."},
            status=status.HTTP_200_OK,
        )


# ── Articles


class ArticleListAPIView(APIView):
    """
    GET  /api/articles/  — List all approved articles.
    POST /api/articles/  — Create a new article (journalists only).
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all approved articles."""
        articles = Article.objects.filter(approved=True)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new article (journalists only)."""
        if not IsJournalist().has_permission(request, self):
            return Response(
                {"error": "Only journalists can create articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ArticleSubscribedAPIView(APIView):
    """
    GET /api/articles/subscribed/
    Returns articles from the reader's subscribed
    publishers/journalists.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return articles from subscribed sources."""
        user = request.user

        journalist_articles = Article.objects.filter(
            approved=True,
            author__in=user.subscribed_journalists.all(),
        )
        publisher_articles = Article.objects.filter(
            approved=True,
            publisher__in=user.subscribed_publishers.all(),
        )
        articles = (journalist_articles | publisher_articles).distinct()

        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


class ArticleDetailAPIView(APIView):
    """
    GET    /api/articles/<id>/  — Retrieve single article.
    PUT    /api/articles/<id>/  — Update (editors/journalists).
    DELETE /api/articles/<id>/  — Delete (editors/journalists).
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_article(self, pk):
        """Helper to get article or return None."""
        try:
            return Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return None

    def get(self, request, pk):
        """Retrieve a single approved article."""
        article = self._get_article(pk)
        if not article or not article.approved:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update an article (editors and journalists only)."""
        if request.user.role not in ("editor", "journalist"):
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        article = self._get_article(pk)
        if not article:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ArticleSerializer(
            article, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete an article (editors and journalists only)."""
        if request.user.role not in ("editor", "journalist"):
            return Response(
                {"error": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        article = self._get_article(pk)
        if not article:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        article.delete()
        return Response(
            {"message": "Article deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class ApproveArticleAPIView(APIView):
    """
    POST /api/articles/<id>/approve/
    Approve an article (editors only).
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Approve an article."""
        if not IsEditor().has_permission(request, self):
            return Response(
                {"error": "Only editors can approve articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            article = Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        article.approved = True
        article.save(update_fields=["approved"])
        return Response(
            {"message": f'Article "{article.title}" approved.'},
            status=status.HTTP_200_OK,
        )


# ── Approved log endpoint (called by signal)


class ApprovedArticleLogAPIView(APIView):
    """
    POST /api/approved/
    Receives and logs approved article data posted by the signal.
    No authentication required (internal use only).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Log an approved article posted by the signal."""
        serializer = ApprovedArticleLogSerializer(data=request.data)
        if serializer.is_valid():
            print(
                f"[APPROVED] Article #{serializer.data['article_id']}"
                f": {serializer.data['title']}"
                f" by {serializer.data['author']}"
            )
            return Response(
                {"message": "Article logged successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


# ── Newsletters


class NewsletterListAPIView(APIView):
    """
    GET  /api/newsletters/  — List all newsletters.
    POST /api/newsletters/  — Create newsletter (journalists only).
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all newsletters."""
        newsletters = Newsletter.objects.all()
        serializer = NewsletterSerializer(newsletters, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a newsletter (journalists only)."""
        if not IsJournalist().has_permission(request, self):
            return Response(
                {"error": "Only journalists can create newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NewsletterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
