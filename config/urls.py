from django.contrib import admin
from django.urls import path

from rest_framework.routers import DefaultRouter

from core.urls import router as core_router
from maakay.urls import router as maakay_router

urlpatterns = [
    path('admin/', admin.site.urls),
]

router = DefaultRouter(trailing_slash=False)
router.registry.extend(core_router.registry)
router.registry.extend(maakay_router.registry)
urlpatterns += router.urls
