"""
Application configuration for LorenasGossip.
Registers signals when the app is ready.
Groups and permissions are created automatically after migrations
via the post_migrate signal — no manual setup required.
"""

from django.apps import AppConfig


class LorenasGossipConfig(AppConfig):
    """Configuration for the LorenasGossip app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "LorenasGossip"

    def ready(self):
        """
        Import signals when the app is ready.
        The import is intentionally inside ready() to avoid
        circular imports — this is the standard Django pattern
        for registering signals.
        """
        import LorenasGossip.signals  # noqa: F401, E402, PLC0415
        from django.db.models.signals import post_migrate
        from LorenasGossip.setup import create_groups_and_permissions
        post_migrate.connect(create_groups_and_permissions, sender=self)
