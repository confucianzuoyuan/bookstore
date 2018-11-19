from rest_framework import serializers
from users.models import Passport

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passport
        fields = ("username", "email")
