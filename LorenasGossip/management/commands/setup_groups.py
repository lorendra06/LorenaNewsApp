"""
Management command to create user groups with correct permissions.
Run with: python manage.py setup_groups
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from LorenasGossip.models import Article, Newsletter


class Command(BaseCommand):
    """Creates Reader, Editor, Journalist, Publisher groups."""

    help = "Creates user groups with correct permissions"

    def handle(self, *args, **options):
        """Create groups and assign permissions."""

        article_ct = ContentType.objects.get_for_model(Article)
        newsletter_ct = ContentType.objects.get_for_model(Newsletter)

        article_perms = Permission.objects.filter(
            content_type=article_ct
        )
        newsletter_perms = Permission.objects.filter(
            content_type=newsletter_ct
        )

        # ── Reader: can only VIEW
        reader_group, _ = Group.objects.get_or_create(name="Reader")
        reader_group.permissions.clear()
        reader_group.permissions.add(
            article_perms.get(codename="view_article"),
            newsletter_perms.get(codename="view_newsletter"),
        )
        self.stdout.write(
            self.style.SUCCESS("Reader group created/updated.")  # pylint: disable=no-member
        )

        # ── Editor: can VIEW, CHANGE, DELETE
        editor_group, _ = Group.objects.get_or_create(name="Editor")
        editor_group.permissions.clear()
        editor_group.permissions.add(
            article_perms.get(codename="view_article"),
            article_perms.get(codename="change_article"),
            article_perms.get(codename="delete_article"),
            newsletter_perms.get(codename="view_newsletter"),
            newsletter_perms.get(codename="change_newsletter"),
            newsletter_perms.get(codename="delete_newsletter"),
        )
        self.stdout.write(
            self.style.SUCCESS("Editor group created/updated.")  # pylint: disable=no-member
        )

        # ── Journalist: can ADD, VIEW, CHANGE, DELETE
        journalist_group, _ = Group.objects.get_or_create(
            name="Journalist"
        )
        journalist_group.permissions.clear()
        journalist_group.permissions.add(
            article_perms.get(codename="add_article"),
            article_perms.get(codename="view_article"),
            article_perms.get(codename="change_article"),
            article_perms.get(codename="delete_article"),
            newsletter_perms.get(codename="add_newsletter"),
            newsletter_perms.get(codename="view_newsletter"),
            newsletter_perms.get(codename="change_newsletter"),
            newsletter_perms.get(codename="delete_newsletter"),
        )
        self.stdout.write(
            self.style.SUCCESS("Journalist group created/updated.")  # pylint: disable=no-member
        )

        # ── Publisher: can VIEW articles/newsletters + manage team
        publisher_group, _ = Group.objects.get_or_create(
            name="Publisher"
        )
        publisher_group.permissions.clear()
        publisher_group.permissions.add(
            article_perms.get(codename="view_article"),
            newsletter_perms.get(codename="view_newsletter"),
        )
        self.stdout.write(
            self.style.SUCCESS("Publisher group created/updated.")  # pylint: disable=no-member
        )

        self.stdout.write(
            self.style.SUCCESS(  # pylint: disable=no-member
                "All groups and permissions set up successfully!"
            )
        )
