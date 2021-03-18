from drf_yasg import openapi
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Demand, Item, User
from .serializers import DemandSerializer, ItemSerializer, RegisterSerializer, LoginSerializer, DemandListSerializer


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user).key
        return Response({'token': token, 'user': serializer.data}, status=status.HTTP_201_CREATED)


class Login(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(username=serializer.data['username'])
        token = Token.objects.get(user=user).key
        return Response({'token': token, 'user': serializer.data}, status=status.HTTP_200_OK)


class DemandListAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DemandListSerializer

    queryset = Demand.objects.all()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @swagger_auto_schema(
        manual_parameters=[Parameter(name='user', in_=openapi.IN_QUERY, type='enum', enum=['client', 'volunteer'])]
    )
    def get(self, request):
        demands = Demand.objects.all()
        user_query = request.query_params.get('user')
        user = self.request.user
        if user_query == 'client':
            demands = demands.filter(client=user)
        elif user_query == 'volunteer':
            demands = demands.filter(volunteer=user)
        serializer = self.serializer_class(data=demands, many=True)
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DemandDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DemandSerializer
    queryset = Demand.objects.all()
    lookup_field = 'id'


class ItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemSerializer
    queryset = Item.objects.all()
    lookup_field = 'id'
