"""
Database models for the LorenasGossip application.
Defines CustomUser, Article, and Newsletter.
Publisher is a CustomUser with role='publisher'.

Modules:
    - CustomUser: Extended user model with role-based access.
    - Article: News article written by a journalist.
    - Newsletter: Curated collection of approved articles.
"""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended user model with role-based fields.

    Roles:
    - reader: can view articles/newsletters, subscribe to
      journalists and publishers.
    - journalist: can write articles and newsletters,
      works with multiple publishers.
    - editor: can approve/delete articles and newsletters,
      works under a publisher.
    - publisher: manages a team of journalists and editors.

    Field separation:
    - Reader fields (subscriptions) are cleared for non-readers.
    - Journalist/Editor fields (publisher team) are cleared
      for non-journalists and non-editors.
    """

    ROLE_CHOICES = [
        ("reader", "Reader"),
        ("journalist", "Journalist"),
        ("editor", "Editor"),
        ("publisher", "Publisher"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="reader",
    )

    # ── Reader-only fields ─────────────────────────────────────────────
    # Cleared (None equivalent) for journalists, editors, publishers.
    subscribed_publishers = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="publisher_subscribers",
        limit_choices_to={"role": "publisher"},
        help_text="Readers only: publishers this reader follows.",
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="followers",
        limit_choices_to={"role": "journalist"},
        help_text="Readers only: journalists this reader follows.",
    )

    # ── Publisher-only fields ──────────────────────────────────────────
    # Publishers manage a team of journalists and editors.
    journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="publisher_journalist_set",
        limit_choices_to={"role": "journalist"},
        help_text="Publisher only: journalists in this team.",
    )
    editors = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="publisher_editor_set",
        limit_choices_to={"role": "editor"},
        help_text="Publisher only: editors in this team.",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        """Auto-assign user to the correct group on save."""
        super().save(*args, **kwargs)
        self._assign_group()
        self._clear_role_fields()

    def _assign_group(self):
        """Remove old role groups and add the correct one."""
        role_group_names = [
            "Reader", "Journalist", "Editor", "Publisher"
        ]
        old_groups = Group.objects.filter(name__in=role_group_names)
        self.groups.remove(*old_groups)
        group, _ = Group.objects.get_or_create(
            name=self.role.capitalize()
        )
        self.groups.add(group)

    def _clear_role_fields(self):
        """
        Enforce role separation by clearing fields that
        do not apply to the user's current role.
        """
        if self.role != "reader":
            # Clear Reader-only subscription fields
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

        if self.role != "publisher":
            # Clear Publisher-only team fields
            self.journalists.clear()
            self.editors.clear()

    # ── Convenience properties ─────────────────────────────────────────

    @property
    def is_reader(self):
        """Return True if user is a reader."""
        return self.role == "reader"

    @property
    def is_journalist(self):
        """Return True if user is a journalist."""
        return self.role == "journalist"

    @property
    def is_editor(self):
        """Return True if user is an editor."""
        return self.role == "editor"

    @property
    def is_publisher(self):
        """Return True if user is a publisher."""
        return self.role == "publisher"

    def get_publishers(self):
        """
        Return all publishers this journalist/editor belongs to.
        Works via reverse relation from publisher's team fields.
        """
        if self.role == "journalist":
            return CustomUser.objects.filter(
                role="publisher",
                publisher_journalist_set=self,
            )
        if self.role == "editor":
            return CustomUser.objects.filter(
                role="publisher",
                publisher_editor_set=self,
            )
        return CustomUser.objects.none()


class Article(models.Model):
    """
    A news article written by a journalist.
    Can be independent or published under a publisher.
    The publisher field links to a CustomUser with role='publisher'.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_articles",
        limit_choices_to={"role": "publisher"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        """Meta options for Article."""

        ordering = ["-created_at"]

    def __str__(self):
        status = "approved" if self.approved else "pending"
        return f"[{status}] {self.title} by {self.author.username}"


class Newsletter(models.Model):
    """A curated collection of articles created by a journalist."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author.username}"
