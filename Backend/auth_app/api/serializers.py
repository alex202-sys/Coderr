from django.contrib.auth.models import User
from rest_framework import serializers
from auth_app.models import UserProfile

from rest_framework.authtoken.models import Token


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model.
    The serializer allows for serialization and deserialization of UserProfile
    instances, including the related User information. The `fullname` field is
    read-only and is generated based on the first and last name of the user."""

    # user = serializers.IntegerField(source="id", read_only=True)

    # fullname = serializers.SerializerMethodField()

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    type = serializers.CharField(source="user.type", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]

        read_only_fields = ["user", "created_at", "uploaded_at"]

    # def get_fullname(self, obj):
    #     """method field `fullname` that combines the first and last name of the
    #     associated User model."""
    #     first = obj.user.first_name
    #     last = obj.user.last_name
    #     name = f"{first} {last}".strip()
    #     return name if name else obj.user.username


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

    # fullname = serializers.CharField(write_only=True)
    # user_id = serializers.IntegerField(source="id", read_only=True)
    # username = serializers.CharField(source="user.username")

    class Meta:
        model = UserProfile
        fields = [
            "token",
            "username",
            "email",
            "password",
            "repeated_password",
            "type",
            # "user_id",
            # 'file',
            # "fullname",
            # "first_name",
            # "last_name",
            # 'location',
            # 'tel',
            # 'description',
            # 'working_hours',
            # 'created_at'
        ]
        # read_only_fields = ["user", "created_at"]
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    # def get_fullname(self, obj):
    #     """method field `fullname` that combines the first and last name of the
    #     associated User model."""
    #     first = obj.first_name
    #     last = obj.last_name
    #     return f"{first} {last}".strip() or obj.username

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
        profile_type = validated_data.pop("type", "customer")
        print(validated_data)
        password = validated_data.get("password")
        username = validated_data.get("username")
        email = validated_data.get("email")
        # Benutzer erstellen und Passwort hashen
        # ser = User.objects.create_user(**validated_data)
        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        # user.set_password(password)
        # user.save()

        # Profil wird automatisch über ein Signal oder direkt hier erstellt
        UserProfile.objects.get_or_create(user=user, type=profile_type)
        return user

    def get_token(self, obj):
        # ohne AbstractUser
        token, _ = Token.objects.get_or_create(ser_id=obj.user_id)
        # from django.apps import apps

        # Holt das Token-Modell dynamisch zur Laufzeit, um den Import-Konflikt zu umgehen
        # TokenModel = apps.get_model("authtoken", "Token")
        # token, _ = TokenModel.objects.get_or_create(user_id=obj.id)
        return token.key

    # def save(self, **kwargs):
    #     try:
    #         fullname = self.validated_data.pop("fullname", "")
    #         parts = fullname.split(" ", 1)
    #         first_name = parts[0]
    #         last_name = parts[1] if len(parts) > 1 else ""
    #         username = first_name or self.validated_data.get("username")

    #         account = User(
    #             email=self.validated_data["email"],
    #             username=username,
    #             first_name=first_name,
    #             last_name=last_name,
    #         )
    #         account.set_password(self.validated_data["password"])
    #         account.save()

    #         UserProfile.objects.create(user=account)
    #         return account
    #     except Exception as e:
    #         raise serializers.ValidationError(
    #             {"server_error": f"Fatal error: {str(e)}"}
    #         )
