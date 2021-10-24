from rest_framework.routers import SimpleRouter

from .views.challenge import ChallengeViewSet
from .views.profile import UserProfileViewSet
from .views.tournament import TournamentViewSet


router = SimpleRouter(trailing_slash=False)
router.register('challenge', ChallengeViewSet)
router.register('profile', UserProfileViewSet)
router.register('tournament', TournamentViewSet)
