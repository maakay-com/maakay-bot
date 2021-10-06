from rest_framework.routers import SimpleRouter

from .views.users import UserViewSet


router = SimpleRouter(trailing_slash=False)
router.register('users', UserViewSet)
