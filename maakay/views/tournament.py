from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from ..models.tournament import Tournament

from ..serializers.tournament import TournamentSerializer


class TournamentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    permission_classes = [IsAdminUser]
