from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from ..models.profile import UserProfile

from ..serializers.profile import UserProfileSerializer


class UserProfileViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
