from django.contrib import admin
from django.urls import path
from .models import CustomDashboard
from .views import AdminDashboardView




@admin.register(CustomDashboard)
class DashboardDummyAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()

        def dashboard_view(request):
            # Pass model_admin to the view
            view = AdminDashboardView.as_view(model_admin=self)
            return view(request)

        custom_view = self.admin_site.admin_view(dashboard_view)
        return [path("", custom_view, name="admin_dashboard")] + urls
