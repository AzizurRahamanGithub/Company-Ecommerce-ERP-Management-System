# employee/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminRole(BasePermission):
    """
    Allow only role=admin or is_superuser.
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (getattr(u, 'role', None) == 'admin' or u.is_superuser))

class HasEmployeeModuleView(BasePermission):
    """
    Requires employee.can_view_employee_module permission for GET
    """
    required_perm = 'employee.can_view_employee_module'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.has_perm(self.required_perm)
        return True  # write checks happen on object or other classes

class HasEmployeeModuleEdit(BasePermission):
    """
    Requires employee.can_edit_employee_module permission for mutating methods
    """
    required_perm = 'employee.can_edit_employee_module'

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return request.user.has_perm(self.required_perm)
        return True
