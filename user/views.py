from rest_framework import viewsets, mixins, authentication, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from django.contrib.auth import get_user_model
from user.serializers import (UserSerializer, TokenSerializer)
from rest_framework import status


# Create your views here.
class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user, many=False)
        return Response(serializer.data)

    @action(detail=False, methods=['PATCH'], permission_classes=[permissions.IsAuthenticated])
    def update_me(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response(serializer.data)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class TokenViewSet(ObtainAuthToken):
    serializer_class = TokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
