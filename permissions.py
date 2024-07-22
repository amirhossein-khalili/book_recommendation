from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerReadOnly(BasePermission):
    message = "permission denied ! you are note owner"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user

    def has_object_permission(self, request, view, obj):

        return obj.user.id == request.user.id


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
