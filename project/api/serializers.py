import datetime

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import Demand, Item, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=20, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'address', 'password']

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
    items = ItemSerializer(many=True, read_only=True)
    client = UserSerializer(read_only=True)
    volunteer = UserSerializer(read_only=True)
    address = serializers.CharField(required=False)

    class Meta:
        model = Demand
        fields = '__all__'
        read_only_fields = ['volunteer', 'client', 'state']


class DemandListSerializer(DemandSerializer):
    items = ItemSerializer(many=True, write_only=True)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        if not items_data:
            raise serializers.ValidationError('There must be at least one item')

        non_duplicates = list()
        for item_data in items_data:
            name = item_data['name']
            if name not in non_duplicates:
                non_duplicates.append(name)
            else:
                raise serializers.ValidationError('Name of each item must be unique for specific demand')

        demand = Demand.objects.create(**validated_data)
        for item_data in items_data:
            Item.objects.create(demand=demand, **item_data)

        user = self.context['request'].user
        if not demand.address:
            demand.address = user.address
        return demand
