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
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from .models import UserProfile
        UserProfile.objects.create(user=instance)



