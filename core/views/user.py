from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from ..models.user import User
from ..serializers.user import UserSerializer


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
