from rest_framework import serializers
from .models import User, Institute


class UserSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField() # TODO: should emails be required?
    password = serializers.CharField(write_only=True)
    institute = serializers.SlugRelatedField(queryset=Institute.objects.all(), slug_field="code") # TODO: make tests to check all works

    def create(self, validated_data):
        user = User.objects.create_user( # type: ignore
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            institute=validated_data["institute"] # NOTE: this is actually an instance, not a code
        )
        return user

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "institute"
        ]

