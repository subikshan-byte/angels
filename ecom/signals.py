from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
import os

from .models import Product, ProductImage


# ---------------- HELPER FUNCTION ----------------
def delete_file(file_field):
    """Safely delete file from storage if it exists."""
    if file_field and hasattr(file_field, "path") and os.path.isfile(file_field.path):
        os.remove(file_field.path)


# ---------------- PRODUCTIMAGE MODEL ----------------
@receiver(post_delete, sender=ProductImage)
def delete_productimage_file_on_row_delete(sender, instance, **kwargs):
    delete_file(instance.image)   # deletes from MEDIA_ROOT/product/images/


@receiver(pre_save, sender=ProductImage)
def delete_old_productimage_file_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_instance = ProductImage.objects.get(pk=instance.pk)
    except ProductImage.DoesNotExist:
        return False

    if old_instance.image != instance.image:
        delete_file(old_instance.image)


# ---------------- PRODUCT MODEL ----------------

# ecom/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def save_google_user_info(request, user, **kwargs):
    socialaccount = user.socialaccount_set.first()
    if socialaccount:
        data = socialaccount.extra_data
        user.email = data.get('email', user.email)
        user.first_name = data.get('given_name', '')
        user.last_name = data.get('family_name', '')
        user.save()


