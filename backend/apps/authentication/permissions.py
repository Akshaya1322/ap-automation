from rest_framework.permissions import BasePermission

from apps.authentication.models import Role


class HasRole(BasePermission):
    """Generic role-gate. Usage: permission_classes = [HasRole.of(Role.ADMIN, Role.AP_MANAGER)]"""

    allowed_roles = ()

    @classmethod
    def of(cls, *roles):
        return type("HasRoleDynamic", (cls,), {"allowed_roles": roles})

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.role in self.allowed_roles or user.is_superuser)
        )


IsAdmin = HasRole.of(Role.ADMIN)
IsAdminOrManager = HasRole.of(Role.ADMIN, Role.AP_MANAGER)
IsFinance = HasRole.of(Role.ADMIN, Role.FINANCE_MANAGER)
CanApprove = HasRole.of(Role.ADMIN, Role.AP_MANAGER, Role.APPROVER, Role.FINANCE_MANAGER)
CanProcessInvoices = HasRole.of(Role.ADMIN, Role.AP_MANAGER, Role.AP_PROCESSOR)
IsAuditor = HasRole.of(Role.ADMIN, Role.AUDITOR)
