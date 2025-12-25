from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStudentOrIsAdmin(BasePermission):
    """Разрешает оплату только аутентифицированным пользователям."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS and request.user.is_authenticated:
            return True
        if view.action == 'pay':
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class ReadOnlyOrIsAdmin(BasePermission):
    """Доступ только администраторам, остальным — только на чтение."""

    def has_permission(self, request, view):
        """Проверка прав доступа."""
        return request.user.is_staff or request.method in SAFE_METHODS
