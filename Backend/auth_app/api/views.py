from django.contrib.auth.models import User
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from auth_app.models import UserProfile
from .serializers import (
    UserProfileSerializerGet,
    UserProfileSerializerPatch,
    RegistrationSerializer,
    UserProfileGetListBusinessSerializer,
    UserProfileGetListCustomerSerializer,
)
from .permissions import IsOwnerByUserProfile


class UserCustomerList(generics.ListAPIView):
    """GET: List all user profiles with type 'customer'."""

    queryset = UserProfile.objects.filter(type=UserProfile.UserType.CUSTOMER)
    serializer_class = UserProfileGetListCustomerSerializer


class UserBusinessList(generics.ListAPIView):
    """GET: List all user profiles with type 'business'."""

    queryset = UserProfile.objects.filter(type=UserProfile.UserType.BUSINESS)
    serializer_class = UserProfileGetListBusinessSerializer


class UserProfileDetail(generics.RetrieveUpdateAPIView):
    """GET: Retrieve a user profile by ID. Only authenticated users
    can access this endpoint.
       PUT/PATCH: Update a user profile, only owner can access this endpoint."""

    queryset = UserProfile.objects.all()
    permission_classes = [IsOwnerByUserProfile]

    def get_serializer_class(self):
        if self.request.method not in permissions.SAFE_METHODS:
            # Logic for POST, PUT, PATCH, DELETE
            return UserProfileSerializerPatch
        return UserProfileSerializerGet


class RegistrationView(generics.CreateAPIView):
    """This endpoint allows anyone to create
    a new user account by providing the required registration details.
    Upon successful registration, an authentication token is generated and returned
    along with the user's information. If the registration data is invalid or
    if there is an error during the registration process, an appropriate error
    message is returned.
    """

    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """POST: Register a new user."""
        serializer = RegistrationSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            try:
                saved_account = serializer.save()
                token, created = Token.objects.get_or_create(user=saved_account)
                data = {
                    "token": token.key,
                    "username": saved_account.username,
                    "email": saved_account.email,
                    "user_id": saved_account.pk,
                }
                return Response(data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(ObtainAuthToken):
    """POST: Log in a user. This endpoint allows registered users to log in by providing
    their email and password. Upon successful authentication, an authentication token
    is generated and returned along with the user's information.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """If the login credentials are invalid or if there is an error during the login
        process, an appropriate error  message is returned."""
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            data = {
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
