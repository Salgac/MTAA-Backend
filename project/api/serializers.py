from django.contrib.auth import authenticate
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


def check_demand_duplicates(validated_data):
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
    return items_data


def create_items_for_demand(items_data, demand):
    for item_data in items_data:
        Item.objects.create(demand=demand, **item_data)


class DemandSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True)
    client = UserSerializer(read_only=True)
    volunteer = UserSerializer(read_only=True)
    address = serializers.CharField(required=False)

    class Meta:
        model = Demand
        fields = '__all__'
        read_only_fields = ['volunteer', 'client', 'state']

    def update(self, instance, validated_data):
        """
        Validation of state flow and user permission for demand update.
        """
        request = self.context['request']
        user = request.user
        # PATCH request for state update
        if self.partial:
            state = request.data['state']
            if instance.state == Demand.State.EXPIRED:
                serializers.ValidationError("Demand has already expired")
            if ((instance.state == Demand.State.CREATED and not state == Demand.State.ACCEPTED) or
                    (instance.state == Demand.State.ACCEPTED and not state == Demand.State.COMPLETED) or
                    (instance.state == Demand.State.COMPLETED and not state == Demand.State.APPROVED)):
                raise serializers.ValidationError(
                    "Demand state cannot be changed from " + str(instance.state) + " to " + str(state))

            if (state == Demand.State.ACCEPTED or state == Demand.State.COMPLETED) and user == instance.client:
                raise serializers.ValidationError("Demand state cannot be changed to " + str(state) + " by client")
            if state == Demand.State.COMPLETED and not user == instance.volunteer:
                raise serializers.ValidationError(
                    "Demand state can be changed to " + str(Demand.State.COMPLETED) + " only by volunteer")
            if state == Demand.State.APPROVED and not user == instance.client:
                raise serializers.ValidationError(
                    "Demand state can be changed to " + str(Demand.State.APPROVED) + " only by client")
        # POST request for demand details update
        else:
            if not user == instance.client:
                raise serializers.ValidationError("Demand can be changed only by client")
            if not instance.state == Demand.State.CREATED:
                raise serializers.ValidationError("Demand can be changed only in state " + str(Demand.State.CREATED))
            # delete old items and create new ones
            Item.objects.filter(demand=instance.id).delete()
            items_data = check_demand_duplicates(validated_data)
            create_items_for_demand(items_data, instance)
        return super().update(instance, validated_data)


class DemandListSerializer(DemandSerializer):
    items = ItemSerializer(many=True, write_only=True)

    def create(self, validated_data):
        items_data = check_demand_duplicates(validated_data)
        demand = Demand.objects.create(**validated_data)
        create_items_for_demand(items_data, demand)
        user = self.context['request'].user
        if not demand.address:
            demand.address = user.address
        return demand
