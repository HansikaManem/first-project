from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import CustomUser   # keep

try:
    from .models import Profile
except ImportError:
    Profile = None   
@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, created, **kwargs):
    if Profile is None:
        return
    if created:
        if instance.role == "driver" and not hasattr(instance, "profile"):
            Profile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()
