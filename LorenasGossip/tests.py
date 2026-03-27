"""
Unit tests for LorenasGossip RESTful API.
Covers authentication, role-based access, subscriptions,
publisher team management, article/newsletter CRUD,
and signal logic.
"""

from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Article, CustomUser, Newsletter


# ── Helpers


def create_user(username, role, password="TestPass123!"):
    """Helper to create a user and return them with a token."""
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@test.com",
        role=role,
    )
    token, _ = Token.objects.get_or_create(user=user)
    return user, token


def auth_client(token):
    """Return an APIClient with token authentication set."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def make_article(author, title="Test Article", approved=True):
    """Helper to create an article with default content."""
    return Article.objects.create(
        title=title,
        content="Test content for the article.",
        author=author,
        approved=approved,
    )


# ── Test: Authentication


class AuthenticationTests(TestCase):
    """Tests for login and token authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user, _ = create_user("testuser", "reader")

    def test_login_with_valid_credentials_returns_token(self):
        """A valid login should return a token."""
        response = self.client.post(
            "/api/login/",
            {"username": "testuser", "password": "TestPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_with_invalid_credentials_returns_401(self):
        """An invalid login should return 401."""
        response = self.client.post(
            "/api/login/",
            {"username": "testuser", "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_to_articles_returns_401(self):
        """Unauthenticated requests should be rejected."""
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_request_to_articles_returns_200(self):
        """Authenticated requests should succeed."""
        _, token = create_user("authuser", "reader")
        client = auth_client(token)
        response = client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ── Test: Role-based access


class RoleBasedAccessTests(
    TestCase
):  # pylint: disable=too-many-instance-attributes
    """Tests for role-based permissions on article endpoints."""

    def setUp(self):
        self.journalist, self.j_token = create_user(
            "journalist1", "journalist"
        )
        self.editor, self.e_token = create_user("editor1", "editor")
        self.reader, self.r_token = create_user("reader1", "reader")
        self.article = make_article(self.journalist)

    def test_journalist_can_create_article(self):
        """Journalists should be able to POST new articles."""
        client = auth_client(self.j_token)
        response = client.post(
            "/api/articles/",
            {"title": "New Article", "content": "Some content here."},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reader_cannot_create_article(self):
        """Readers should NOT be able to POST articles."""
        client = auth_client(self.r_token)
        response = client.post(
            "/api/articles/",
            {"title": "Reader Article", "content": "Some content."},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_cannot_create_article(self):
        """Editors should NOT be able to POST articles."""
        client = auth_client(self.e_token)
        response = client.post(
            "/api/articles/",
            {"title": "Editor Article", "content": "Some content."},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_approve_article(self):
        """Editors should be able to approve articles."""
        unapproved = make_article(
            self.journalist, title="Unapproved", approved=False
        )
        client = auth_client(self.e_token)
        response = client.post(f"/api/articles/{unapproved.pk}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unapproved.refresh_from_db()
        self.assertTrue(unapproved.approved)

    def test_reader_cannot_approve_article(self):
        """Readers should NOT be able to approve articles."""
        unapproved = make_article(
            self.journalist, title="Unapproved", approved=False
        )
        client = auth_client(self.r_token)
        response = client.post(f"/api/articles/{unapproved.pk}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_delete_article(self):
        """Editors should be able to delete articles."""
        client = auth_client(self.e_token)
        response = client.delete(f"/api/articles/{self.article.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_reader_cannot_delete_article(self):
        """Readers should NOT be able to delete articles."""
        client = auth_client(self.r_token)
        response = client.delete(f"/api/articles/{self.article.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_roles_can_view_articles(self):
        """All authenticated roles should be able to view articles."""
        for token in [self.j_token, self.e_token, self.r_token]:
            client = auth_client(token)
            response = client.get("/api/articles/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


# ── Test: Publisher team management


class PublisherTests(TestCase):  # pylint: disable=too-many-instance-attributes
    """Tests for publisher team management via API."""

    def setUp(self):
        self.publisher, self.p_token = create_user("publisher1", "publisher")
        self.journalist, self.j_token = create_user(
            "journalist1", "journalist"
        )
        self.editor, self.e_token = create_user("editor1", "editor")
        self.reader, self.r_token = create_user("reader1", "reader")

    def test_all_roles_can_view_publishers(self):
        """All authenticated users can view the publisher list."""
        for token in [self.p_token, self.j_token, self.e_token, self.r_token]:
            client = auth_client(token)
            response = client.get("/api/publishers/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_journalist_can_join_publisher(self):
        """Journalists should be able to join a publisher's team."""
        client = auth_client(self.j_token)
        response = client.post(f"/api/publishers/{self.publisher.pk}/join/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.publisher.refresh_from_db()
        self.assertIn(self.journalist, self.publisher.journalists.all())

    def test_editor_can_join_publisher(self):
        """Editors should be able to join a publisher's team."""
        client = auth_client(self.e_token)
        response = client.post(f"/api/publishers/{self.publisher.pk}/join/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.publisher.refresh_from_db()
        self.assertIn(self.editor, self.publisher.editors.all())

    def test_reader_cannot_join_publisher(self):
        """Readers should NOT be able to join a publisher's team."""
        client = auth_client(self.r_token)
        response = client.post(f"/api/publishers/{self.publisher.pk}/join/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journalist_can_leave_publisher(self):
        """Journalists should be able to leave a publisher's team."""
        self.publisher.journalists.add(self.journalist)
        client = auth_client(self.j_token)
        response = client.post(f"/api/publishers/{self.publisher.pk}/leave/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.publisher.refresh_from_db()
        self.assertNotIn(self.journalist, self.publisher.journalists.all())

    def test_publisher_can_manage_team(self):
        """Publisher should be able to update their team via API."""
        client = auth_client(self.p_token)
        response = client.post(
            f"/api/publishers/{self.publisher.pk}/team/",
            {
                "journalist_ids": [self.journalist.pk],
                "editor_ids": [self.editor.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.publisher.refresh_from_db()
        self.assertIn(self.journalist, self.publisher.journalists.all())
        self.assertIn(self.editor, self.publisher.editors.all())

    def test_journalist_cannot_manage_publishers_team(self):
        """Journalists should NOT be able to manage a publisher's team."""
        client = auth_client(self.j_token)
        response = client.post(
            f"/api/publishers/{self.publisher.pk}/team/",
            {"journalist_ids": [self.journalist.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ── Test: Reader subscriptions


class SubscriptionTests(TestCase):
    """Tests for reader subscription-based article filtering."""

    def setUp(self):
        self.journalist1, _ = create_user("journo1", "journalist")
        self.journalist2, _ = create_user("journo2", "journalist")
        self.reader, self.r_token = create_user("reader1", "reader")

        self.subscribed_article = make_article(
            self.journalist1, title="Subscribed Article"
        )
        make_article(self.journalist2, title="Other Article")
        self.reader.subscribed_journalists.add(self.journalist1)

    def test_subscribed_endpoint_returns_only_subscribed_articles(self):
        """Reader should only see articles from subscribed sources."""
        client = auth_client(self.r_token)
        response = client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        titles = [a["title"] for a in response.data]
        self.assertIn("Subscribed Article", titles)
        self.assertNotIn("Other Article", titles)

    def test_subscribed_includes_publisher_articles(self):
        """Reader subscribed to a publisher sees its articles."""
        publisher, _ = create_user("pub1", "publisher")
        Article.objects.create(
            title="Publisher Article",
            content="Content for publisher article.",
            author=self.journalist2,
            publisher=publisher,
            approved=True,
        )
        self.reader.subscribed_publishers.add(publisher)

        client = auth_client(self.r_token)
        response = client.get("/api/articles/subscribed/")
        titles = [a["title"] for a in response.data]
        self.assertIn("Publisher Article", titles)

    def test_reader_with_no_subscriptions_sees_empty_list(self):
        """A reader with no subscriptions sees an empty list."""
        _, token = create_user("emptyreader", "reader")
        client = auth_client(token)
        response = client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


# ── Test: Newsletters


class NewsletterTests(TestCase):
    """Tests for newsletter creation and access."""

    def setUp(self):
        self.journalist, self.j_token = create_user("journo1", "journalist")
        self.reader, self.r_token = create_user("reader1", "reader")
        self.article = make_article(
            self.journalist, title="Article for Newsletter"
        )

    def test_journalist_can_create_newsletter(self):
        """Journalists should be able to create newsletters."""
        client = auth_client(self.j_token)
        response = client.post(
            "/api/newsletters/",
            {
                "title": "My Newsletter",
                "description": "A test newsletter.",
                "article_ids": [self.article.pk],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reader_cannot_create_newsletter(self):
        """Readers should NOT be able to create newsletters."""
        client = auth_client(self.r_token)
        response = client.post(
            "/api/newsletters/",
            {"title": "Reader Newsletter", "description": "Fails."},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_roles_can_view_newsletters(self):
        """All authenticated users should be able to view newsletters."""
        Newsletter.objects.create(
            title="Test Newsletter",
            author=self.journalist,
        )
        for token in [self.j_token, self.r_token]:
            client = auth_client(token)
            response = client.get("/api/newsletters/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


# ── Test: Signal logic


class SignalTests(TestCase):
    """
    Tests for signal logic on article approval.
    Uses mocking to avoid real emails and HTTP requests.
    """

    def setUp(self):
        self.journalist, _ = create_user("journo1", "journalist")
        self.subscriber, _ = create_user("subscriber1", "reader")
        self.subscriber.subscribed_journalists.add(self.journalist)

    @patch("LorenasGossip.signals._post_to_api")
    @patch("LorenasGossip.signals._send_approval_emails")
    def test_signal_fires_on_article_approval(self, mock_email, mock_post):
        """
        When an article is approved, both email and API
        post functions should be called.
        """
        article = make_article(
            self.journalist,
            title="Signal Test Article",
            approved=False,
        )
        article.approved = True
        article.save(update_fields=["approved"])

        mock_email.assert_called_once_with(article)
        mock_post.assert_called_once_with(article)

    @patch("LorenasGossip.signals._post_to_api")
    @patch("LorenasGossip.signals._send_approval_emails")
    def test_signal_does_not_fire_when_not_approved(
        self, mock_email, mock_post
    ):
        """
        Saving an unapproved article should NOT trigger
        email or API post.
        """
        make_article(
            self.journalist,
            title="Unapproved Article",
            approved=False,
        )
        mock_email.assert_not_called()
        mock_post.assert_not_called()

    @patch("LorenasGossip.signals.requests.post")
    @patch("LorenasGossip.signals.send_mail")
    def test_email_sent_to_subscribers_on_approval(
        self, mock_mail, mock_requests_post
    ):
        """Subscribers should receive an email when article approved."""
        article = make_article(
            self.journalist,
            title="Email Test Article",
            approved=False,
        )
        article.approved = True
        article.save(update_fields=["approved"])

        self.assertTrue(mock_mail.called)
        call_kwargs = mock_mail.call_args
        recipient_list = call_kwargs[1].get(
            "recipient_list",
            call_kwargs[0][3] if len(call_kwargs[0]) > 3 else [],
        )
        self.assertIn(self.subscriber.email, recipient_list)
        _ = mock_requests_post  # required by mock, verified implicitly
