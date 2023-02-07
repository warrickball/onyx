from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError
import django.contrib.auth.password_validation as validators

# from utils import fieldserializers


class UserSerializer(serializers.ModelSerializer):
    # username = fieldserializers.LowerCharField() # TODO: understand why having validators here wiped validators on model
    # email = fieldserializers.LowerCharField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        # User.objects.create_user() hashes the password
        user = User.objects.create_user(  # type: ignore
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            site=validated_data["site"],
        )
        return user

    def validate(self, data):
        # https://stackoverflow.com/a/36419160/16088113
        errors = {}
        user = User(**data)
        password = data.get("password")

        try:
            validators.validate_password(password=password, user=user)
        except ValidationError as e:
            errors["password"] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        return data

    class Meta:
        model = User
        fields = ["username", "password", "email", "site"]


class SiteWaitingUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "site", "date_joined"]


class AdminWaitingUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "site",
            "date_site_approved",
        ]
