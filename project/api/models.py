from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager)
from django.db import models

ADDRESS_LENGTH = 80


class UserManager(BaseUserManager):
    def create_user(self, username, address, password=None):
        if username is None:
            raise TypeError('Username is required')
        if address is None:
            raise TypeError('Address is required')
        if password is None:
            raise TypeError('Password is required')
        user = self.model(username=username, address=address)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=20, unique=True, db_index=True)
    address = models.CharField(max_length=ADDRESS_LENGTH)
    avatar = models.BinaryField()
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'

    objects = UserManager()

    def __str__(self):
        return self.username


class Demand(models.Model):
    class State(models.TextChoices):
        CREATED = 'created'
        ACCEPTED = 'accepted'
        COMPLETED = 'completed'
        APPROVED = 'approved'
        EXPIRED = 'expired'

    title = models.CharField(max_length=20)
    address = models.CharField(max_length=ADDRESS_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client')
    volunteer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='volunteer', blank=True, null=True)
    state = models.CharField(choices=State.choices, default=State.CREATED, max_length=20)

    def __str__(self):
        str(self.title)


class Item(models.Model):
    class Unit(models.TextChoices):
        PIECES = 'pcs'
        KILOGRAM = 'kg'

    name = models.CharField(max_length=20)
    quantity = models.DecimalField(decimal_places=2, max_digits=5)
    unit = models.CharField(choices=Unit.choices, max_length=5)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        str(self.name)
