from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from auth_app.models import UserProfile
import re


class UserProfileGetListCustomerSerializer(serializers.ModelSerializer):
    """Serializer for the list UserProfile model, filter by Customer .."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type",
        ]

    def to_representation(self, instance):
        """'file' fix "" if Null"""
        data = super().to_representation(instance)
        if data.get("file") is None:
            data["file"] = ""
        return data


class UserProfileGetListBusinessSerializer(serializers.ModelSerializer):
    """Serializer for the list UserProfile model, filter by Business .."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
        ]

    def to_representation(self, instance):
        """'file' fix "" if Null"""
        data = super().to_representation(instance)
        if data.get("file") is None:
            data["file"] = ""
        return data


class UserProfileSerializerPatch(serializers.ModelSerializer):
    """Owner by UserProfil should Userprofil wreite"""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]

        read_only_fields = [
            "user",
            "username",
            "file",
            "created_at",
            "uploaded_at",
            "type",
        ]

    def to_representation(self, instance):
        """'file' fix "" if Null"""
        data = super().to_representation(instance)
        if data.get("file") is None:
            data["file"] = ""
        return data

    def update(self, instance, validated_data):
        """Extract the nested user data (if present). Since we are using
        `source="user.username"`, DRF provides us with a `user` dictionary here."""

        user_data = validated_data.pop("user", None)
        # First, update the standard fields of the UserProfile (e.g., location, tel, description)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Now update the data of the linked standard user.
        if user_data:
            user = instance.user
            if "email" in user_data:
                user.email = user_data["email"]
            if "first_name" in user_data:
                user.first_name = user_data["first_name"]
            if "last_name" in user_data:
                user.last_name = user_data["last_name"]

            user.username = f"{user.first_name.lower()}_{user.last_name.lower()}"
            user.save()

        return instance


class UserProfileSerializerGet(serializers.ModelSerializer):
    """Serializer for the UserProfile model.
    The serializer allows for serialization and deserialization of UserProfile
    instances, including the related User information. The `fullname` field is
    read-only and is generated based on the first and last name of the user."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            # "uploaded_at",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]

        read_only_fields = ["user", "created_at", "uploaded_at", "type"]

    def to_representation(self, instance):
        user = instance.user
        if user.username and (not user.first_name or not user.last_name):
            if "_" in user.username:
                parts = user.username.split("_", 1)
            else:
                # re.split looks for an uppercase letter [A-Z]
                # The r'(?=[A-Z])' syntax ensures the split occurs before the letter,
                # without removing the uppercase letter itself.
                split_parts = re.split(r"(?=[A-Z])", user.username, maxsplit=1)

                # If an uppercase letter is found, we have 2 parts
                if len(split_parts) == 2:
                    parts = split_parts

            if not user.first_name:
                # Capitalize the first letter
                user.first_name = parts[0].capitalize()
            if not user.last_name:
                user.last_name = parts[1].capitalize() if len(parts) > 1 else ""
            user.save()

        data_inst = super().to_representation(instance)
        # 'file' fix "" if Null
        if data_inst.get("file") is None:
            data_inst["file"] = ""

        return data_inst


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration. It includes fields for email, fullname, and password confirmation.
    The serializer validates that the email is unique and that the password and repeated password match.
    """

    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    token = serializers.SerializerMethodField()
    type = serializers.CharField(default="customer")

    class Meta:
        model = UserProfile
        fields = [
            "token",
            "username",
            "email",
            "password",
            "repeated_password",
            "type",
        ]
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate_email(self, value):
        """_check user with the same email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with the same email already exists")
        return value

    def validate_username(self, value):
        """_check user with the same username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("The User is already exists")
        return value

    def validate(self, data):
        """check repeated password and password"""
        if data.get("password") != data.get("repeated_password"):
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        password = validated_data.get("password")
        profile_type = validated_data.pop("type", "customer")
        print(validated_data)
        username = validated_data.get("username")
        email = validated_data.get("email")
        parts = []
        if "_" in username:
            parts = username.split("_", 1)
        else:
            split_parts = re.split(r"(?=[A-Z])", username, maxsplit=1)
            if len(split_parts) == 2:
                parts = split_parts
        if parts:
            first_name = parts[0].capitalize()
            last_name = parts[1].capitalize() if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Profile is created automatically via a signal or directly here
        UserProfile.objects.get_or_create(user=user, type=profile_type)
        return user

    def get_token(self, obj):
        # without AbstractUser
        token, _ = Token.objects.get_or_create(user_id=obj.user_id)
        return token.key
