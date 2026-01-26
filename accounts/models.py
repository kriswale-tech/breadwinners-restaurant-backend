from django.db import models
from utils.models import TimeStampedSoftDeleteModel
from .managers import SoftDeleteUserModel
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from django.conf import settings

# User model
class User(SoftDeleteUserModel, AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return self.email

# Profile model
class Profile(TimeStampedSoftDeleteModel):
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        STAFF = 'staff', 'Staff'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, choices=RoleChoices.choices)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

