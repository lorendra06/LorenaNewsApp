"""
Django signals for LorenasGossip.
Triggered after an article is saved and approved:
  1. Sends email to all subscribers of the journalist or publisher.
  2. POSTs the approved article to /api/approved/ endpoint.
"""

import requests
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article


@receiver(post_save, sender=Article)
def on_article_approved(sender, instance, **kwargs):
    """
    Fires after every Article save.
    Only acts when the article has just been approved.
    The sender argument is required by Django's signal API.
    """
    _ = sender  # required by Django signal API

    if not instance.approved:
        return

    update_fields = kwargs.get("update_fields")
    if update_fields and "approved" not in update_fields:
        return

    _send_approval_emails(instance)
    _post_to_api(instance)


def _collect_subscriber_emails(article):
    """
    Collect emails of all subscribers for the article's
    journalist or publisher.

    - Followers of the journalist (readers who subscribed
      to this journalist via subscribed_journalists field).
    - Subscribers of the publisher (readers who subscribed
      to this publisher via subscribed_publishers field).
      The reverse relation is 'publisher_subscribers'.
    """
    emails = set()

    # Readers subscribed to this journalist
    for subscriber in article.author.followers.all():
        if subscriber.email:
            emails.add(subscriber.email)

    # Readers subscribed to this publisher (if article has one)
    if article.publisher:
        for subscriber in article.publisher.publisher_subscribers.all():
            if subscriber.email:
                emails.add(subscriber.email)

    return list(emails)


def _send_approval_emails(article):
    """Send the approved article to all relevant subscribers."""
    recipient_emails = _collect_subscriber_emails(article)

    if not recipient_emails:
        return

    subject = f"New Article: {article.title}"
    message = (
        f"A new article has been published!\n\n"
        f"Title: {article.title}\n"
        f"Author: {article.author.username}\n\n"
        f"{article.content[:500]}...\n\n"
        f"Visit the site to read the full article."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email="noreply@lorenasgossip.com",
        recipient_list=recipient_emails,
        fail_silently=True,
    )


def _post_to_api(article):
    """
    POST approved article data to the internal /api/approved/ endpoint.
    Simulates sharing the article externally.
    """
    payload = {
        "article_id": article.pk,
        "title": article.title,
        "author": article.author.username,
        "publisher": (
            article.publisher.username if article.publisher else None
        ),
    }

    try:
        requests.post(
            "http://127.0.0.1:8000/api/approved/",
            json=payload,
            timeout=5,
        )
    except requests.exceptions.RequestException:
        pass
