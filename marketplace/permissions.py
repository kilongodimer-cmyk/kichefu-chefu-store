from rest_framework.permissions import BasePermission, SAFE_METHODS


class ProposalPermission(BasePermission):
    """Allow public proposal creation, restrict reads/updates to staff users."""

    def has_permission(self, request, view):
        if request.method == "POST":
            return True
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_staff)
        return bool(request.user and request.user.is_staff)
