"""
Forms for the LorenasGossip application.
Handles registration, article/newsletter creation,
and publisher team management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Article, CustomUser, Newsletter


class RegisterForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    """Registration form with role selection and validation."""

    email = forms.EmailField(required=True)

    class Meta:
        """Meta options for RegisterForm."""

        model = CustomUser
        fields = ("username", "email", "role", "password1", "password2")

    def clean_email(self):
        """Validate that email is not already in use."""
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise ValidationError("Email address is required.")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        """Validate that username is long enough."""
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username is required.")
        if len(username) < 3:
            raise ValidationError(
                "Username must be at least 3 characters long."
            )
        return username

    def clean_role(self):
        """Validate that the selected role is valid."""
        role = self.cleaned_data.get("role")
        valid_roles = ["reader", "journalist", "editor", "publisher"]
        if role not in valid_roles:
            raise ValidationError(
                f"Invalid role. Choose from: {', '.join(valid_roles)}"
            )
        return role

    def save(self, commit=True):
        """Save user and trigger group assignment."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class PublisherTeamForm(forms.ModelForm):
    """
    Form for publishers to manage their team.
    Allows selecting journalists and editors.
    """

    journalists = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role="journalist"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label="Journalists",
        help_text="Select journalists for your team.",
    )
    editors = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role="editor"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label="Editors",
        help_text="Select editors for your team.",
    )

    class Meta:
        """Meta options for PublisherTeamForm."""

        model = CustomUser
        fields = ("journalists", "editors")


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles with validation."""

    def __init__(self, *args, user=None, **kwargs):
        """
        Filter publisher choices to only publishers
        that include this journalist in their team.
        Uses the reverse relation 'publisher_journalist_set'
        which returns all publishers where this user
        appears in their 'journalists' field.
        """
        super().__init__(*args, **kwargs)
        if user and user.role == "journalist":
            # Find publishers that have this journalist in their team
            self.fields["publisher"].queryset = CustomUser.objects.filter(
                role="publisher",
                journalists=user,
            )
        else:
            self.fields["publisher"].queryset = CustomUser.objects.filter(
                role="publisher"
            )

    class Meta:
        """Meta options for ArticleForm."""

        model = Article
        fields = ("title", "content", "publisher")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 8}
            ),
            "publisher": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_title(self):
        """Validate article title length."""
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        if len(title) > 255:
            raise ValidationError("Title cannot exceed 255 characters.")
        return title

    def clean_content(self):
        """Validate article content length."""
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise ValidationError("Content is required.")
        if len(content) < 20:
            raise ValidationError(
                "Content must be at least 20 characters long."
            )
        return content


class NewsletterForm(forms.ModelForm):
    """Form for creating and editing newsletters with validation."""

    class Meta:
        """Meta options for NewsletterForm."""

        model = Newsletter
        fields = ("title", "description", "articles")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def clean_title(self):
        """Validate newsletter title length."""
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_articles(self):
        """Validate that only approved articles are included."""
        articles = self.cleaned_data.get("articles", [])
        for article in articles:
            if not article.approved:
                raise ValidationError(
                    f'Article "{article.title}" is not approved yet '
                    f"and cannot be added to a newsletter."
                )
        return articles
