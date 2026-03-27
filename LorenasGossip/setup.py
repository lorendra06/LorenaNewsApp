"""
Automatic setup for LorenasGossip groups and permissions.
Called via post_migrate signal after every migration run.
No manual commands required.
"""


def create_groups_and_permissions(sender, **kwargs):
    """
    Create user groups and assign permissions automatically
    after migrations are applied.

    Groups created:
    - Reader: view articles and newsletters
    - Editor: view, change, delete articles and newsletters
    - Journalist: add, view, change, delete articles and newsletters
    - Publisher: view articles and newsletters
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from .models import Article, Newsletter

    # Get content types
    try:
        article_ct = ContentType.objects.get_for_model(Article)
        newsletter_ct = ContentType.objects.get_for_model(Newsletter)
    except Exception:  # noqa: BLE001
        # Tables may not exist yet during initial migration
        return

    def get_perm(ct, codename):
        """Safely retrieve a permission by content type and codename."""
        try:
            return Permission.objects.get(
                content_type=ct, codename=codename
            )
        except Permission.DoesNotExist:
            return None

    # Article permissions
    article_view = get_perm(article_ct, "view_article")
    article_add = get_perm(article_ct, "add_article")
    article_change = get_perm(article_ct, "change_article")
    article_delete = get_perm(article_ct, "delete_article")

    # Newsletter permissions
    newsletter_view = get_perm(newsletter_ct, "view_newsletter")
    newsletter_add = get_perm(newsletter_ct, "add_newsletter")
    newsletter_change = get_perm(newsletter_ct, "change_newsletter")
    newsletter_delete = get_perm(newsletter_ct, "delete_newsletter")

    # ── Reader: can only VIEW
    reader_group, _ = Group.objects.get_or_create(name="Reader")
    reader_group.permissions.set(
        [p for p in [article_view, newsletter_view] if p]
    )

    # ── Editor: can VIEW, CHANGE, DELETE
    editor_group, _ = Group.objects.get_or_create(name="Editor")
    editor_group.permissions.set([p for p in [
        article_view, article_change, article_delete,
        newsletter_view, newsletter_change, newsletter_delete,
    ] if p])

    # ── Journalist: can ADD, VIEW, CHANGE, DELETE
    journalist_group, _ = Group.objects.get_or_create(
        name="Journalist"
    )
    journalist_group.permissions.set([p for p in [
        article_add, article_view, article_change, article_delete,
        newsletter_add, newsletter_view, newsletter_change,
        newsletter_delete,
    ] if p])

    # ── Publisher: can VIEW articles and newsletters
    publisher_group, _ = Group.objects.get_or_create(name="Publisher")
    publisher_group.permissions.set(
        [p for p in [article_view, newsletter_view] if p]
    )
