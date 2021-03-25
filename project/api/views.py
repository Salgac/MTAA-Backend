from drf_yasg import openapi
from drf_yasg.openapi import Parameter, Schema
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework.exceptions import ParseError
from PIL import Image
from django.core.files import File

from .models import Demand, Item, User
from .serializers import (
    DemandSerializer,
    UserSerializer,
    ItemSerializer,
    RegisterSerializer,
    LoginSerializer,
    DemandListSerializer,
)


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    badRequestPropertySchema = Schema(
        type=openapi.TYPE_ARRAY, items=Schema(type=openapi.TYPE_STRING)
    )

    @swagger_auto_schema(
        operation_description="Register new user",
        responses={
            200: RegisterSerializer(),
            400: Schema(
                type=openapi.TYPE_OBJECT,
                title="Error: Bad Request",
                properties={
                    "username": badRequestPropertySchema,
                    "password": badRequestPropertySchema,
                    "address": badRequestPropertySchema,
                },
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user).key
        return Response(
            {"token": token, "user": serializer.data}, status=status.HTTP_201_CREATED
        )


class Login(generics.GenericAPIView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        operation_description="Authenticate user",
        responses={
            200: LoginSerializer(),
            401: Schema(
                type=openapi.TYPE_OBJECT,
                title="Error: Unauthorized",
                properties={"detail": Schema(type=openapi.TYPE_STRING)},
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(username=serializer.data["username"])
        token = Token.objects.get(user=user).key
        return Response(
            {"token": token, "user": serializer.data}, status=status.HTTP_200_OK
        )


class ImageView(generics.GenericAPIView):
    serializer_class = UserSerializer
    parser_classes = [FileUploadParser]

    def put(self, request, name, filename):
        # validate request data in serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        path = "avatars/" + name + ".jpg"

        # test for file in data
        if "file" not in request.data:
            raise ParseError("Empty content.")

        # open and save image
        img = Image.open(request.data["file"])
        img.save(path)

        # get user and save the image
        user = User.objects.get(username=name)
        user.avatar = path
        user.save()

        # render response
        return Response(
            {"user": user.username, "file_path": user.avatar.url},
            status=status.HTTP_200_OK,
        )


class DemandListAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DemandListSerializer

    queryset = Demand.objects.all()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @swagger_auto_schema(
        manual_parameters=[
            Parameter(
                name="user",
                in_=openapi.IN_QUERY,
                type="enum",
                enum=["client", "volunteer"],
            ),
            Parameter(name="address", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request):
        demands = Demand.objects.all()
        user_query = request.query_params.get("user")
        user = self.request.user
        if user_query == "client":
            demands = demands.filter(client=user)
        elif user_query == "volunteer":
            demands = demands.filter(volunteer=user)

        address_query = request.query_params.get("address")
        if address_query is not None:
            demands = demands.filter(address__icontains=address_query)
        serializer = self.serializer_class(data=demands, many=True)
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DemandDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DemandSerializer
    queryset = Demand.objects.all()
    lookup_field = "id"


class ItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemSerializer
    queryset = Item.objects.all()
    lookup_field = "id"
