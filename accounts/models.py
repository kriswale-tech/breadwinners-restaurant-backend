from django.db import models
from utils.models import TimeStampedSoftDeleteModel
from .managers import SoftDeleteUserModel
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from shops.models import Shop
from django.conf import settings
from django.core.exceptions import ValidationError

# User model
class User(SoftDeleteUserModel, AbstractUser):
    username = None
    phone_number = models.CharField(max_length=20, unique=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.phone_number}"

# Profile model
class Profile(TimeStampedSoftDeleteModel):
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        STAFF = 'staff', 'Staff'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, choices=RoleChoices.choices)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="profiles", null=True, blank=True)

    @property
    def is_staff(self):
        return self.role == self.RoleChoices.STAFF

    @property
    def is_admin(self):
        return self.role == self.RoleChoices.ADMIN

    def clean(self):
        if self.role == self.RoleChoices.STAFF and not self.shop:
            raise ValidationError("Staff must be assigned to a shop.")

        if self.role == self.RoleChoices.ADMIN and self.shop:
            raise ValidationError("Admin should not be assigned to a shop.")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

