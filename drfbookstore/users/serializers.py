from rest_framework.validators import UniqueValidator
import re
from datetime import datetime, timedelta
from drfbookstore.settings import REGEX_MOBILE
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "gender", "birthday", "email", "mobile")

class UserRegSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label="用户名", help_text="用户名", required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="用户已经存在")])
    password = serializers.CharField(
        style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True,
    )

    # 不加字段名的验证器作用于所有字段之上。attrs是字段validate之后返回的总的dict
    def validate(self, attrs):
        attrs["mobile"] = attrs["username"]
        return attrs

    class Meta:
        model = User
        fields = ("username", "mobile", "password")

