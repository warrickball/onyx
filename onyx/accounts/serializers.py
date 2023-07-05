from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError
import django.contrib.auth.password_validation as validators


class CreateUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def create(self, validated_data):
        username = validated_data["last_name"] + validated_data["first_name"][:1]
        increment = 0

        while User.objects.filter(
            username=f"{username}{increment if increment else ''}"
        ).exists():
            increment += 1

        if increment:
            username = f"{username}{increment}"

        # This function handles password hashing
        return User.objects.create_user(  #  type: ignore
            username=username,
            email=validated_data["email"],
            password=validated_data["password"],
            site=validated_data["site"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )

    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError(
                "This field must only contain alphabetic characters."
            )
        return value

    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError(
                "This field must only contain alphabetic characters."
            )
        return value

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
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "site",
            "password",
        ]


class ViewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "site",
        ]


class SiteWaitingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "site",
            "date_joined",
        ]


class AdminWaitingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "site",
            "when_site_approved",
        ]
