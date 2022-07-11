from rest_framework import serializers
from .models import User
from data.serializers import get_choices
from data.models import Uploader


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField() # TODO: including this enforces that it is required. Why?
    password = serializers.CharField(write_only=True)
    uploader = serializers.ChoiceField(choices=get_choices(model=Uploader, field="code"))

    def create(self, validated_data):
        user = User.objects.create_user( # type: ignore
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            uploader=validated_data["uploader"]
        )
        return user

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "uploader"
        ]
