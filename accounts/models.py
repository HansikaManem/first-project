from cProfile import Profile
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

def next_status(current):
    return STATUS_FLOW.get(current)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (("customer", "Customer"), ("driver", "Driver"))

    email = models.EmailField(unique=True)
    role  = models.CharField(max_length=10, choices=ROLE_CHOICES)

    USERNAME_FIELD  = "email"          
    REQUIRED_FIELDS = ["username"]     

    def __str__(self):
        return self.email


STATUS_FLOW = {
    "accepted": "in_transit",
    "in_transit": "delivered",
}

def next_status(current):
    return STATUS_FLOW.get(current_status)  # type: ignore


class DeliveryRequest(models.Model):
    STATUS_CHOICES = [
        ("pending",  "Pending"),
        ("accepted", "Accepted"),
        ("picked",   "Picked-Up"),
        ('in_transit', 'In Transit'),
        ("delivered","Delivered"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_requests"
    )
    pickup_address  = models.CharField(max_length=255)
    dropoff_address = models.CharField(max_length=255)
    package_note    = models.CharField(max_length=255)
    status          = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]          

    def __str__(self):
        return f"{self.pk} | {self.customer.email} | {self.status}"


User = get_user_model()

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deliveries')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_deliveries')

    # Old fields 
    address = models.CharField(max_length=255)
    package_details = models.TextField()

    # New structured fields 
    pickup_address = models.CharField(max_length=255)
    dropoff_address = models.CharField(max_length=255)
    package_note = models.TextField(blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto populate old fields based on new ones
        self.address = f"{self.pickup_address} to {self.dropoff_address}"
        self.package_details = self.package_note or "No additional notes"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Delivery #{self.id} - {self.status}"



ALLOWED_STATUS_TRANSITIONS = {
    "Accepted": "In Transit",
    "In Transit": "Delivered",
}

class Feedback(models.Model):
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback for Delivery {self.delivery.id}"

User = get_user_model()

#class Profile(models.Model):  
#   user = models.OneToOneField(User, on_delete=models.CASCADE)
#   phone = models.CharField(max_length=15, blank=True)
#  profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
# def __str__(self):
#    return f"{self.user.username}'s Profile"
    
#@receiver(post_save, sender=CustomUser)
#def create_user_profile(sender, instance, created, **kwargs):
#    if created and instance.role == 'driver':
#        Profile.objects.create(user=instance)
# changed