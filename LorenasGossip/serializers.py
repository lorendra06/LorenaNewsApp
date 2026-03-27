"""
DRF serializers for Article, Newsletter, and CustomUser.
Publisher is a CustomUser with role='publisher'.
"""

from rest_framework import serializers

from .models import Article, CustomUser, Newsletter


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model (read-only public info)."""

    class Meta:
        """Meta options for CustomUserSerializer."""

        model = CustomUser
        fields = ("id", "username", "email", "role")
        read_only_fields = ("id", "role")


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for Publisher profile.
    A Publisher is a CustomUser with role='publisher'.
    Includes team counts and member lists.
    """

    journalist_count = serializers.SerializerMethodField()
    editor_count = serializers.SerializerMethodField()
    journalist_names = serializers.SerializerMethodField()
    editor_names = serializers.SerializerMethodField()

    class Meta:
        """Meta options for PublisherSerializer."""

        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "journalist_count",
            "editor_count",
            "journalist_names",
            "editor_names",
        )
        read_only_fields = ("id",)

    def get_journalist_count(self, obj):
        """Return number of journalists in the team."""
        return obj.journalists.count()

    def get_editor_count(self, obj):
        """Return number of editors in the team."""
        return obj.editors.count()

    def get_journalist_names(self, obj):
        """Return list of journalist usernames."""
        return list(obj.journalists.values_list("username", flat=True))

    def get_editor_names(self, obj):
        """Return list of editor usernames."""
        return list(obj.editors.values_list("username", flat=True))


class PublisherTeamSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a publisher's team.
    Accepts journalist_ids and editor_ids for team management.
    """

    journalist_ids = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="journalist"),
        source="journalists",
        many=True,
        required=False,
    )
    editor_ids = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="editor"),
        source="editors",
        many=True,
        required=False,
    )
    journalists = CustomUserSerializer(many=True, read_only=True)
    editors = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        """Meta options for PublisherTeamSerializer."""

        model = CustomUser
        fields = (
            "id",
            "username",
            "journalists",
            "journalist_ids",
            "editors",
            "editor_ids",
        )
        read_only_fields = ("id", "username")

    def update(self, instance, validated_data):
        """Update publisher's team members."""
        if "journalists" in validated_data:
            instance.journalists.set(validated_data["journalists"])
        if "editors" in validated_data:
            instance.editors.set(validated_data["editors"])
        return instance


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model."""

    author = CustomUserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="publisher"),
        source="publisher",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        """Meta options for ArticleSerializer."""

        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "publisher_id",
            "approved",
            "created_at",
        )
        read_only_fields = ("id", "author", "approved", "created_at")


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for Newsletter model."""

    author = CustomUserSerializer(read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)
    article_ids = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.filter(approved=True),
        source="articles",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        """Meta options for NewsletterSerializer."""

        model = Newsletter
        fields = (
            "id",
            "title",
            "description",
            "author",
            "articles",
            "article_ids",
            "created_at",
        )
        read_only_fields = ("id", "author", "created_at")


class ApprovedArticleLogSerializer(serializers.Serializer):
    """
    Serializer for the /api/approved/ endpoint.
    Logs approved article data posted by the signal.
    Read-only — create and update are not needed.
    """

    article_id = serializers.IntegerField()
    title = serializers.CharField()
    author = serializers.CharField()
    publisher = serializers.CharField(allow_null=True, required=False)

    def create(self, validated_data):
        """Not implemented — this serializer is read-only."""
        raise NotImplementedError("ApprovedArticleLogSerializer is read-only.")

    def update(self, instance, validated_data):
        """Not implemented — this serializer is read-only."""
        raise NotImplementedError("ApprovedArticleLogSerializer is read-only.")
