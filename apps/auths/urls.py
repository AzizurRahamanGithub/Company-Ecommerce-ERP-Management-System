from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    LoginView,
    ProtectedView,
    LogoutView,
    GetNewAccessTokenView,
    ForgotPasswordView,
    PasswordChangeView,
    ResetPasswordView,
    ProfileView,
    GoogleOauth,
    ResendVerificationEmailAPIView,
    DetailSingleProfile,
    AdminUserView,
    DeliveryRoleListView,
    MyAddressListCreateView, MyAddressDetailView
)
from .views import ResendOTPAPIView, UserAPIView, UserDetailAPIView, RegisterAPIView

router = DefaultRouter()
router.register(r"admin/users", AdminUserView, basename="user")


urlpatterns = [
    path("", include(router.urls)),
    # --- register
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("resend-otp/", ResendOTPAPIView.as_view(), name="resend-otp"),
    # --- login and logout
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("protected-endpoint/", ProtectedView.as_view(), name="protected"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("token/refresh/", GetNewAccessTokenView.as_view(), name="token_refresh"),
    # --- password_change
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path(
        "resend-email-link/",
        ResendVerificationEmailAPIView.as_view(),
        name="resent-email",
    ),
    # --forgot_password
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path(
        "reset-password/<uidb64>/<token>/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    # ---- google auth
    path("google/", GoogleOauth.as_view(), name="google_login"),
    path("profile/<int:pk>/", UserDetailAPIView.as_view(), name="detail_profile"),
    # delivery role
    path("delivery-role/", DeliveryRoleListView.as_view(), name="delivery-role-list"),
    path("addresses/", MyAddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:pk>/", MyAddressDetailView.as_view(), name="address-detail"),
]
