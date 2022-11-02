from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, Institute
from django.core.exceptions import ValidationError
import django.contrib.auth.password_validation as validators
from utils import fieldserializers


class UserSerializer(serializers.ModelSerializer):
    username = fieldserializers.LowerCharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = fieldserializers.LowerCharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True)
    institute = serializers.SlugRelatedField(
        queryset=Institute.objects.all(), slug_field="code"
    )

    def create(self, validated_data):
        # User.objects.create_user() hashes the password
        user = User.objects.create_user(  # type: ignore
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            institute=validated_data["institute"],
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
        fields = ["username", "password", "email", "institute"]


class InstituteWaitingUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "institute", "date_joined"]


class AdminWaitingUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "institute",
            "date_institute_approved",
        ]
