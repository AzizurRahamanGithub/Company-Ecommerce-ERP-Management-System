# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser
# from django.utils import timezone
# from unfold.admin import ModelAdmin
# from django.contrib import admin
# from django.urls import path
# from django.shortcuts import render
# from django.utils.translation import gettext_lazy as _
# from .forms import SingleImageForm, MultipleImagesForm
# from django.contrib.auth.forms import ReadOnlyPasswordHashField


# class CustomUserAdmin(ModelAdmin):
#     form = type(
#         "CustomUserSingleImageForm",
#         (SingleImageForm,),
#         {
#             "Meta": type("Meta", (SingleImageForm.Meta,), {"model": CustomUser}),
#             "image_folder": "customUser",
#             "password": ReadOnlyPasswordHashField(
#                 help_text=(
#                     '<a href="../password/" '
#                     'style="display:inline-block; padding:6px 16px; '
#                     'border:1px solid #667eea; border-radius:6px; '
#                     'color:#667eea; text-decoration:none; font-size:13px; '
#                     'font-weight:500; margin-top:6px; '
#                     'transition: all 0.2s;" '
#                     'onmouseover="this.style.background=\'#667eea\';this.style.color=\'#fff\'" '
#                     'onmouseout="this.style.background=\'transparent\';this.style.color=\'#667eea\'"'
#                     '>🔑 Change Password</a>'
#                 )
#             ),
#         },
#     )
#     model = CustomUser
#     list_display = (
#         "email", "id", "username", "first_name", "last_name",
#         "role", "is_active", "is_staff", "is_superuser", "stripe_customer_id",
#     )
#     list_filter = ("role", "is_active", "is_staff", "is_superuser")  # ✅ এটাই যথেষ্ট
#     search_fields = ("email", "username", "first_name", "last_name", "phone_number")
#     ordering = ("-id",)
#     fieldsets = (
#         (None, {"fields": ("email", "username", "password", "stripe_customer_id")}),
#         (
#             "Personal info",
#             {
#                 "fields": (
#                     ("full_name", "first_name", "last_name", "role", "phone_number", "address"),
#                     "upload_image",
#                     "delete_image",
#                 )
#             },
#         ),
#         (
#             "Permissions",
#             {
#                 "fields": (
#                     "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
#                 )
#             },
#         ),
#     )
#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": ("email", "username", "password1", "password2", "role", "is_active"),
#             },
#         ),
#     )
    
#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context['action_form'] = self.action_form(auto_id=None)
#         return super().changelist_view(request, extra_context=extra_context)

#     def get_queryset(self, request):
#             return super().get_queryset(request)

#     # --- Custom Admin URLs ---
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path(
#                 "admins/",
#                 self.admin_site.admin_view(self.view_admins),
#                 name="customuser_admins",
#             ),
#             path(
#                 "staff/",
#                 self.admin_site.admin_view(self.view_staff),
#                 name="customuser_staff",
#             ),
#             path(
#                 "users/",
#                 self.admin_site.admin_view(self.view_users),
#                 name="customuser_users",
#             ),
#             path(
#                 "<id>/password/",
#                 self.admin_site.admin_view(self.user_change_password),
#                 name="auth_user_password_change",
#             ),
#         ]
#         return urls + custom_urls

#     def view_admins(self, request):
#         qs = self.model.objects.filter(is_superuser=True)
#         context = dict(
#             self.admin_site.each_context(request),
#             title=_("Admin Users"),
#             users=qs,
#             section="Admins",
#         )
#         return render(request, "customuser_list.html", context)

#     def view_staff(self, request):
#         qs = self.model.objects.filter(is_staff=True, is_superuser=False)
#         context = dict(
#             self.admin_site.each_context(request),
#             title=_("Staff Members"),
#             users=qs,
#             section="Staff",
#         )
#         return render(request, "customuser_list.html", context)

#     def view_users(self, request):
#         qs = self.model.objects.filter(is_staff=False, is_superuser=False)
#         context = dict(
#             self.admin_site.each_context(request),
#             title=_("Regular Users"),
#             users=qs,
#             section="Users",
#         )
#         return render(request, "customuser_list.html", context)


# # Register models
# admin.site.register(CustomUser, CustomUserAdmin)


# # @admin.register(UserProfile)
# # class UserProfileAdmin(admin.ModelAdmin):
# #     list_display = ('user', 'otp', 'otp_created_at', 'reset_token', 'reset_token_expires')
# #     search_fields = ('user__email', 'user__username')



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from unfold.admin import ModelAdmin
from django.urls import path
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from .forms import SingleImageForm
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class CustomUserAdmin(UserAdmin, ModelAdmin):  # ✅ দুটোই inherit করুন
    form = type(
        "CustomUserSingleImageForm",
        (SingleImageForm,),
        {
            "Meta": type("Meta", (SingleImageForm.Meta,), {"model": CustomUser}),
            "image_folder": "customUser",
            "password": ReadOnlyPasswordHashField(
                help_text=(
                    '<a href="../password/" '
                    'style="display:inline-block; padding:6px 16px; '
                    'border:1px solid #667eea; border-radius:6px; '
                    'color:#667eea; text-decoration:none; font-size:13px; '
                    'font-weight:500; margin-top:6px; '
                    'transition: all 0.2s;" '
                    'onmouseover="this.style.background=\'#667eea\';this.style.color=\'#fff\'" '
                    'onmouseout="this.style.background=\'transparent\';this.style.color=\'#667eea\'"'
                    '>🔑 Change Password</a>'
                )
            ),
        },
    )
    model = CustomUser
    list_display = (
        "email", "id", "username", "first_name", "last_name",
        "role", "is_active", "is_staff", "is_superuser", "stripe_customer_id",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "username", "first_name", "last_name", "phone_number")
    ordering = ("-id",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password", "stripe_customer_id")}),
        (
            "Personal info",
            {
                "fields": (
                    ("full_name", "first_name", "last_name", "role", "phone_number", "address"),
                    "upload_image",
                    "delete_image",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "role", "is_active"),
            },
        ),
    )
    # ✅ get_urls(), view_admins, view_staff, view_users — সব বাদ
    


admin.site.register(CustomUser, CustomUserAdmin)