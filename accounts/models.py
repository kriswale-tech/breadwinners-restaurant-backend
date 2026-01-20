from django.db import models
from utils.models import TimeStampedSoftDeleteModel, SoftDeleteUserModel
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from django.conf import settings

# User model
class User(SoftDeleteUserModel, AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return self.email

# Role model
class Role(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'

    name = models.CharField(max_length=255, choices=RoleChoices.choices)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# Profile model
class Profile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.PROTECT) # Prevent role from being deleted if associated with a profile

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"

