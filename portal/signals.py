from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

ROLES = ("student", "parent", "teacher", "admin")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_profile(sender, instance, created, **kwargs):
    """Keep the portal's role in step with the user.

    If your user model has its own `role` field (yours does), that field is the one place to
    set a person's role and the portal copies it. Otherwise new accounts start as students
    and the role is changed on the Profile.
    """
    role = getattr(instance, "role", None)
    if role in ROLES:
        Profile.objects.update_or_create(user=instance, defaults={"role": role})
    elif created:
        Profile.objects.get_or_create(
            user=instance, defaults={"role": "admin" if instance.is_superuser else "student"})