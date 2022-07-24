from rest_framework import serializers
from .models import User, Institute
from utils.functions import get_choices


class UserSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField() # TODO: including this enforces that it is required. Why?
    password = serializers.CharField(write_only=True)

    # TODO: adding a new institute requires the server be restarted for it to be a valid choice. This way of doing it doesn't work!!!!!!!!!!
    institute = serializers.ChoiceField(choices=get_choices(model=Institute, field="code")) # TODO: Accounts can be made before institute is, so this isn't working properly

    def create(self, validated_data):
        user = User.objects.create_user( # type: ignore
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            institute=validated_data["institute"]
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
