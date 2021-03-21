from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import Demand, Item, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=20, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'address', 'password']

    def validate(self, attrs):
        username = attrs.get('username', '')
        address = attrs.get('address', '')
        if not username.isalnum():
            raise serializers.ValidationError('The username should only contain alphanumeric characters')
        if address is None:
            raise serializers.ValidationError('Address is required')
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=20, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'address', 'avatar', 'password']
        read_only_fields = ['address', 'avatar']

    def validate(self, attrs):
        username = attrs.get('username', '')
        password = attrs.get('password', '')
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'address', 'avatar']
        read_only_fields = ['username', 'address', 'avatar']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['demand']


class DemandSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True)
    client = UserSerializer(read_only=True)
    volunteer = UserSerializer(read_only=True)

    class Meta:
        model = Demand
        fields = '__all__'
        read_only_fields = ['volunteer', 'client', 'state']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        demand = Demand.objects.create(**validated_data)
        for item_data in items_data:
            Item.objects.create(demand=demand, **item_data)
        return demand


class DemandListSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    volunteer = UserSerializer(read_only=True)

    class Meta:
        model = Demand
        fields = '__all__'
        read_only_fields = ['volunteer', 'client', 'state']
