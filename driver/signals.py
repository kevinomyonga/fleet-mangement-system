from .models import Driver
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


@receiver(post_save, sender=Driver)
def create_order_history_for_driver(sender, instance, **kwargs):
    if instance.id is None:
        pass
    else:
        pass