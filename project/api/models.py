import datetime

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from rest_framework import serializers

ADDRESS_LENGTH = 80


class UserManager(BaseUserManager):
    def create_user(self, username, address, password=None):
        if username is None:
            raise TypeError("Username is required")
        if address is None:
            raise TypeError("Address is required")
        if password is None:
            raise TypeError("Password is required")
        user = self.model(username=username, address=address)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=20, unique=True, db_index=True)
    address = models.CharField(max_length=ADDRESS_LENGTH)
    avatar = models.ImageField(upload_to="avatars/")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"

    objects = UserManager()

    def __str__(self):
        return self.username


class DemandManager(models.Manager):
    def get_queryset(self):
        queryset = super(DemandManager, self).get_queryset()
        queryset.filter(expired_at__lt=timezone.now()).update(
            state=Demand.State.EXPIRED
        )
        return queryset


class Demand(models.Model):
    objects = DemandManager()

    class State(models.TextChoices):
        CREATED = "created"
        ACCEPTED = "accepted"
        COMPLETED = "completed"
        APPROVED = "approved"
        EXPIRED = "expired"

    title = models.CharField(max_length=20)
    address = models.CharField(max_length=ADDRESS_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client")
    volunteer = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="volunteer",
        blank=True,
        null=True,
    )
    state = models.CharField(
        choices=State.choices, default=State.CREATED, max_length=20
    )

    def __str__(self):
        str(self.title)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # if demand can be changed, verify expired_at time
        if (
            self.state == Demand.State.CREATED
            and self.expired_at < timezone.now() + datetime.timedelta(days=1)
        ):
            raise serializers.ValidationError(
                "Expiration time must be in more than 24 hours from now"
            )

        # the demand is being created
        if self.created_at is None:
            client_demands = Demand.objects.all().filter(client=self.client)
            if client_demands.filter(title=self.title):
                raise serializers.ValidationError(
                    "Demand with given title already exists"
                )

        super().save(force_insert, force_update, using, update_fields)


class Item(models.Model):
    class Unit(models.TextChoices):
        PIECES = "pcs"
        KILOGRAM = "kg"

    name = models.CharField(max_length=20)
    quantity = models.DecimalField(decimal_places=2, max_digits=5)
    unit = models.CharField(choices=Unit.choices, max_length=5)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name="items")

    class Meta:
        unique_together = (
            "demand",
            "name",
        )

    def __str__(self):
        str(self.name)
