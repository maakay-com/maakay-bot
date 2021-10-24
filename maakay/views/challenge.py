from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from ..models.challenge import Challenge

from ..serializers.challenge import ChallengeSerializer


class ChallengeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsAdminUser]
