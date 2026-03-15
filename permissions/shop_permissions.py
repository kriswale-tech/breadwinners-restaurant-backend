from rest_framework.permissions import BasePermission
from accounts.models import Profile

class IsShopMember(BasePermission):
    """
    Allow admins globally; staff only within their own shop scope.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False

        if profile.role == Profile.RoleChoices.ADMIN:
            return True

        # Non-admin users must match the shop id in URL kwargs.
        return profile.shop_id == view.kwargs.get('shop_id')