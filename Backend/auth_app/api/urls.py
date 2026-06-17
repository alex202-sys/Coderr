from django.urls import include, path
from .views import (
    RegistrationView,
    UserLoginView,
    UserProfileDetail,
    UserBusinessList,
    UserCustomerList,
)

urlpatterns = [
    path("profiles/customer/", UserCustomerList.as_view(), name="usercustomer-list"),
    path("profiles/business/", UserBusinessList.as_view(), name="userbusiness-list"),
    path("profile/<int:pk>/", UserProfileDetail.as_view(), name="userprofile-detail"),
    path("registration/", RegistrationView.as_view(), name="api-registration"),
    path("login/", UserLoginView.as_view(), name="api-login"),
]
