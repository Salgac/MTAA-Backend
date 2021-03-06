from PIL import Image
from django.db.models import Q
from django.http import FileResponse
from drf_yasg import openapi
from drf_yasg.openapi import Parameter, Schema
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics, serializers, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Demand, User
from .serializers import (
    DemandSerializer,
    UserSerializer,
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
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser]

    def put(self, request):
        # validate request data in serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get user
        user = self.request.user
        path = "avatar/" + user.username + ".png"

        # open, resize and save image
        imageFile = request._request.FILES.get("file")
        img = Image.open(imageFile)
        img = img.resize((300, 300), Image.ANTIALIAS)
        img.save(path)

        user.avatar = path
        user.save()

        # render response
        return Response(
            {"file_path": user.avatar.url},
            status=status.HTTP_200_OK,
        )


class AvatarView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get avatar by username",
        responses={
            200: Schema(type=openapi.TYPE_FILE),
        },
    )
    def get(self, request, filename):
        # validate name
        try:
            img = open("avatar/" + filename, "rb")
        except FileNotFoundError:
            img = open("avatar/default.png", "rb")

        # return
        response = FileResponse(img)
        return response


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
                enum=["client", "volunteer", "none"],
            ),
            Parameter(
                name="state",
                in_=openapi.IN_QUERY,
                type="enum",
                enum=["created", "accepted", "completed", "approved", "expired"],
            ),
            Parameter(name="address", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
    )
    def get(self, request):
        demands = Demand.objects.all().filter().order_by("expired_at")
        user_query = request.query_params.get("user")
        user = self.request.user
        if user_query == "client":
            demands = demands.filter(client=user)
        elif user_query == "volunteer":
            demands = demands.filter(volunteer=user)
        elif user_query == "none":
            demands = demands.filter(~Q(client=user), ~Q(volunteer=user))

        state_query = request.query_params.get("state")
        if state_query is not None:
            demands = demands.filter(state=state_query)

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

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        state = request.data["state"]
        if state == Demand.State.ACCEPTED:
            serializer.save(volunteer=request.user, state=state)
        else:
            serializer.save(state=state)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        user = self.request.user
        if not user == instance.client:
            raise serializers.ValidationError("Demand can be deleted only by client")
        super().perform_destroy(instance)
